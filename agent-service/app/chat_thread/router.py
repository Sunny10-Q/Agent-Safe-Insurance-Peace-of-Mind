from fastapi import APIRouter, Depends
from .crud import ChatThreadService
from .schemas import ChatThreadCreate, ChatThreadResponse
from ..core.database import get_db
from app.core.logging import get_logger

logger = get_logger(__name__)

# 定义路由
router=APIRouter(prefix="/chat-threads")

# 注入session获取crud实例
async def get_chat_thread_service(session=Depends(get_db)):
    return ChatThreadService(session)

@router.get("/hi")
async def say_hi():
    return 'hi 安心保欢迎您'


user_id=1
# 新增会话
@router.post("")
async def create_chat(request:ChatThreadCreate,chat_thread_crud:ChatThreadService=Depends(get_chat_thread_service))->ChatThreadResponse:

    result= await chat_thread_crud.create_chat(user_id,request.title)
    logger.info(f"创建会话成功，会话id:{result.id}")
    return result
