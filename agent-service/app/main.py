import sys
import time
from contextlib import asynccontextmanager
import structlog
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
import asyncio
from starlette.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.database import init_db,close_db


# 初始化日志配置
configure_logging(level=settings.log_level, log_format=settings.log_format)
logger = get_logger(__name__)

# 生命周期管理（预留）
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("agent_service_starting", app_version=settings.app_version)
        # 初始化数据库
        await init_db()
        yield
    finally:
        logger.info("agent_service_stopping")
        # 项目停止时关闭数据库
        await close_db()

# 初始化FastAPI
app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

# 日志输出中间件
@app.middleware("http")
async def add_log_uuid(request: Request, call_next):
    # 1. 清理并生成新的请求上下文
    structlog.contextvars.clear_contextvars()
    request_id = str(uuid.uuid4())

    # 2. 绑定当前请求的核心信息
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
    )

    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)

    # 3. 记录请求结束日志
    logger.info("request_processed", status_code=response.status_code, duration=f"{duration_ms:.4f}ms")
    return response

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins="http://127.0.0.1:5173",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def healthy():
    return {"status": "running", "port": "8001"}

if __name__ == "__main__":
    import uvicorn
    # 启动命令：python -m app.main
    config = uvicorn.Config(
        "app.main:app",
        host="0.0.0.0",
        port=settings.app_port,
        reload=False
    )
    server = uvicorn.Server(config)

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(server.serve())
    else:
        server.run()