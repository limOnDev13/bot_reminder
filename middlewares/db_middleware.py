"""
Модуль, отвечающий за мидлварь, которая взаимодействует с базой данных
"""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from asyncpg.pool import Pool
from database import DataBaseClass


class DataBaseMiddleware(BaseMiddleware):
    def __init__(self, pool: Pool):
        super().__init__()
        self.pool = pool

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        async with self.pool.acquire() as connect:
            data['database'] = DataBaseClass(connect)
            return await handler(event, data)
