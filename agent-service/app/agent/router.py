
from fastapi import APIRouter, Request, Depends, HTTPException
from langchain_core.messages import HumanMessage
from langgraph.graph.state import CompiledStateGraph

from app.agent.schemas import ChatRequest
from app.chat_thread.schemas import ChatThreadResponse
from app.core.logging import get_logger

logger = get_logger(__name__)

# 定义路由
router=APIRouter()


# 获取Agent
def get_agent(request: Request):
    # 从FastApi中获取全局Agent
    return request.app.state.agent

@router.post("/chat")
async def chat(
        request: ChatRequest,
        agent : CompiledStateGraph = Depends(get_agent)
):
    # 校验请求参数
    if not request.thread_id:
        raise HTTPException(status_code=422,detail="Thread ID 不能为空")
    if not request.message:
        raise HTTPException(status_code=422,detail="message 不能为空")

    # 组织输入参数
    _input = {'messages':[HumanMessage(content=request.message)]}
    # 会话id
    config = {"configurable":{"thread_id":request.thread_id}}
    # 调用模型
    response = await agent.ainvoke(_input,config)
    # 返回结果
    return response['messages'][-1].content