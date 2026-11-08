from sqlalchemy.ext.asyncio import AsyncSession

from app.chat_thread.models import ChatThreadTable
from app.chat_thread.schemas import ChatThreadResponse



class ChatThreadService:

    def __init__(self,session:AsyncSession):
        self._session:AsyncSession =session

    # 新增会话
    async def create_chat(self,user_id:int,title:str)-> ChatThreadTable:
        # 自动开始事务
        async with self._session.begin() as session:
            chat_thread = ChatThreadTable(user_id=user_id,title=title)
            # 操作数据库新增
            self._session.add(chat_thread)
            return chat_thread
