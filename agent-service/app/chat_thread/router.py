from fastapi import APIRouter

# 定义路由
router=APIRouter(prefix="/chat-threads")

@router.get("/hi")
async def say_hi():
    return 'hi 安心保欢迎您'