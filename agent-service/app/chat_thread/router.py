from fastapi import APIRouter, Depends, HTTPException,Request
from langgraph.graph.state import CompiledStateGraph
from starlette import status
from uuid import UUID

from app.chat_thread.crud import ChatThreadService
from .exceptions import ChatThreadNotFound
from .schemas import ChatThreadCreate, ChatThreadResponse, ChatHistoryResponse
from ..core.database import get_db
from app.core.logging import get_logger
from app.agent.service import get_history_messages,delete_history_message

logger = get_logger(__name__)

# 定义路由
router=APIRouter(prefix="/chat-threads")

# 注入session获取crud实例
async def get_chat_thread_service(session=Depends(get_db)):
    return ChatThreadService(session)

# 注入agent
def get_agent(request: Request) -> CompiledStateGraph:
    return request.app.state.agent

@router.get("/hi")
async def say_hi():
    return 'hi 安心保欢迎您'


user_id=1
# 新增会话
@router.post("")
async def create_chat(request:ChatThreadCreate,chat_thread_crud:ChatThreadService=Depends(get_chat_thread_service))->ChatThreadResponse:
    # 创建新会话
    result= await chat_thread_crud.create_chat(user_id,request.title)
    logger.info(f"创建会话成功，会话id:{result.id}")
    return result



# 查询当前用户所有会话
@router.get("",response_model=list[ChatThreadResponse],status_code=status.HTTP_200_OK)
async def get_chat_list(chat_thread_service:ChatThreadService=Depends(get_chat_thread_service))->list[ChatThreadResponse]:
    # 查询当前用户会话列表
    result= await chat_thread_service.get_chat_list(user_id)
    logger.info(f"查询用户{user_id}的会话列表，共{len(result)}条")
    return result # type: ignore


# 重命名会话
@router.patch("/{thread_id}", response_model=ChatThreadResponse)
async def rename_chat_thread(
    thread_id: UUID,
    body: ChatThreadCreate,
    chat_thread_service: ChatThreadService = Depends(get_chat_thread_service),
) -> ChatThreadResponse:
    """重命名会话"""
    try:
        thread = await chat_thread_service.rename(thread_id, user_id, body.title)
        logger.info(f"会话重命名成功id:{thread_id}")
    except ChatThreadNotFound as exc:
        # 异常转换
        raise _not_found() from exc
    logger.info("chat_thread_renamed", thread_id=str(thread_id), user_id=user_id)
    return thread

# 删除会话
@router.delete("/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_thread(
        thread_id: UUID,
        chat_thread_service: ChatThreadService = Depends(get_chat_thread_service)
):
    try:
        await chat_thread_service.delete(thread_id, user_id)
        # TODO 删除会话历史消息
        logger.info(f"删除会话成功，会话id:{thread_id}")
    except ChatThreadNotFound as exc:
        raise _not_found() from exc


# 查询会话
@router.get("/{thread_id}/messages")
async def get_message_history(
        thread_id: UUID,
        agent:CompiledStateGraph=Depends(get_agent),
        chat_thread_service: ChatThreadService = Depends(get_chat_thread_service),
)->ChatHistoryResponse:
    # 校验，当前会话是否属于当前用户
    await chat_thread_service.require_owner(thread_id,user_id)
    # 查询会话历史
    messages = await get_history_messages(agent,thread_id)
    # 封装结果
    return ChatHistoryResponse(thread_id=thread_id ,messages=messages)



@router.delete("/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_thread(
    thread_id: UUID,
    agent: CompiledStateGraph=Depends(get_agent),
    chat_thread_service: ChatThreadService = Depends(get_chat_thread_service)
):
    try:
        # 删除会话
        await chat_thread_service.delete(thread_id, user_id)
        # 删除会话历史消息
        await delete_history_message(agent, thread_id)

        logger.info("删除会话成功~", thread_id=str(thread_id), user_id=user_id)

    except ChatThreadNotFound as ex:
        raise _not_found() from ex


# 定义通用的404异常方法
def _not_found() -> HTTPException:
    return HTTPException(status_code=404, detail="chat chat_thread not found")

