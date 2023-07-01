from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from asyncpg.pool import Pool
from models.models import DataBaseClass


class DataBaseMiddleware(BaseMiddleware):
    def __init__(self, pool: Pool):
        super().__init__()
        self.pool = pool

    def __call__(self,
                 handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                 event: TelegramObject,
                 data: Dict[str, Any]
                 ) -> Any:
        data['database'] = DataBaseClass(self.pool)
        return await handler(event, data)
