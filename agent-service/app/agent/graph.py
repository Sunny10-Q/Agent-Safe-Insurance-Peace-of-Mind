from langchain.chat_models import init_chat_model
from langgraph.constants import START, END
from langgraph.graph import MessagesState, StateGraph
from app.core.config import settings

# 创建Agent
async def create_agent(checkpointer):

    # 定义大模型
    llm = init_chat_model(
        settings.chat_model, # 模型名称
        extra_body={'thinking': {'type': 'disabled'}} #关闭思考
    )

    # 定义节点
    async def llm_node(state: MessagesState):
        # 直接对话
        response = await llm.ainvoke(state['messages'])
        # 返回结果
        return {'messages': [response]}

    # 构建图
    builder = StateGraph(MessagesState)
    # 构建节点
    builder.add_node('llm', llm_node)
    # 构建边
    builder.add_edge(START, 'llm')
    builder.add_edge('llm', END)

    #编译
    graph = builder.compile(checkpointer)
    return graph



