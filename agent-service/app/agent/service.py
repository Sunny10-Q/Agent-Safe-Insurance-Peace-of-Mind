from typing import AsyncGenerator
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph.state import CompiledStateGraph

from app.chat_thread.schemas import ChatHistoryMessage
from app.chat_thread.crud import ChatThreadService
from app.core.database import get_session_factory
from app.core.logging import get_logger

logger = get_logger(__name__)

# 流式对话
async def chat_steam(agent:CompiledStateGraph,message:str,thread_id:str,decision:dict)->AsyncGenerator[dict,None]:
    # 对话时同步更新会话活跃时间
    SessionFactory = get_session_factory()
    async with SessionFactory() as session:
        await ChatThreadService(session).touch(thread_id)

    # 组织输入参数
    _input = {'messages': [HumanMessage(content=message)]}
    # 会话id
    config = {"configurable": {"thread_id": thread_id}}
    # 调用模型
    response = agent.astream(
        _input,
        config,
        stream_mode='messages',
        version='v2'
    )
    # response中的结构
    # {
    #     ‘type’:'messages',
    #     'data':(AIMessage,Metadata)
    # }

    # 返回结果(从流中取出结果，返回ServerSentEvent)
    async for chunk in response:
        if chunk['type'] == 'messages':
            token, metadata = chunk['data']
            if isinstance(token, AIMessage) and token.content:
                yield {'event': 'message','data': token.content}
    yield {'event':'done','data':'END'}


# 查询会话历史
async def get_history_messages(agent:CompiledStateGraph, thread_id: str)->list[ChatHistoryMessage]:
    #记忆的thread_id
    config={'configurable': {'thread_id': thread_id}}
    # 获取state
    state = await agent.aget_state(config)
    # 获取消息
    values = state.values
    if not values or not values.get('messages'):
        return []
    messages = values.get('messages')
    # 将messages转换成ChatHistoryMessage
    history_messages = []
    for message in messages:
        if isinstance(message, HumanMessage):
            history_messages.append(ChatHistoryMessage(role='user',content=message.content))
        elif isinstance(message, AIMessage):
            history_messages.append(ChatHistoryMessage(role='assistant',content=message.content))

    return history_messages


# 删除会话历史
async def delete_history_message(agent:CompiledStateGraph, thread_id: str):
    """删除会话历史"""
    await agent.checkpointer.adelete_thread(thread_id)