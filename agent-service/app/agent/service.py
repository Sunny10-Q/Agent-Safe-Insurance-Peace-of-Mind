from typing import AsyncGenerator
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph.state import CompiledStateGraph


async def chat_steam(agent:CompiledStateGraph,message:str,thread_id:str,decision:dict)->AsyncGenerator[dict,None]:
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
