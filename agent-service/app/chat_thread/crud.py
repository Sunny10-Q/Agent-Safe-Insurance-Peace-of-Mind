from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat_thread.exceptions import ChatThreadNotFound
from app.chat_thread.models import ChatThreadTable



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

    # 查询所有会话
    async def get_chat_list(self,user_id:int)->list[ChatThreadTable]:

        result = await self._session.execute(
            select(ChatThreadTable).where(ChatThreadTable.user_id == user_id).order_by(desc(ChatThreadTable.updated_at), desc(ChatThreadTable.created_at)) # type: ignore
        )

        return result.scalars().all() # type: ignore

    # 会话重命名
    async def rename(self, thread_id, user_id, title)->ChatThreadTable:
        async with self._session.begin():
            result = await self._session.execute(
                update(ChatThreadTable)
                .values(title=title)
                .where(ChatThreadTable.user_id == user_id, ChatThreadTable.id == thread_id)
                .returning(ChatThreadTable)
            )
            # 判断是否更新成功
            thread = result.scalar_one_or_none()
            if thread is None:
                raise ChatThreadNotFound
            # 返回结果
            return thread

