
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.sse import EventSourceResponse, ServerSentEvent
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph.state import CompiledStateGraph

from app.agent.schemas import ChatRequest
from app.chat_thread.schemas import ChatThreadResponse
from app.core.logging import get_logger
from app.agent.service import chat_steam

logger = get_logger(__name__)

# 定义路由
router=APIRouter()


# 获取Agent
def get_agent(request: Request):
    # 从FastApi中获取全局Agent
    return request.app.state.agent

@router.post("/chat",response_class=EventSourceResponse)
async def chat(
        request: ChatRequest,
        agent : CompiledStateGraph = Depends(get_agent)
):
    # 校验请求参数
    if request.thread_id is None:
        raise HTTPException(status_code=422,detail="Thread ID 不能为空")
    if request.message is None and request.decision is None:
        raise HTTPException(status_code=422,detail="message 或 decision 不能为空")

    # 调用chat_stream
    async for chunk in chat_steam(agent,request.message,request.thread_id,request.decision):
        yield ServerSentEvent(event=chunk['event'],data=chunk['data'])



