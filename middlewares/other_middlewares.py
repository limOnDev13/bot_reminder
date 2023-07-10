"""
Модуль, отвечающий за различные миддлвари, которые не попали в другие файлы
"""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from database import TodayRemindersClass


# Миддлварь, которая будет пробрасывать в хэндлеры объект TodayRemindersClass
class TodayRemindersMiddleware(BaseMiddleware):
    def __init__(self, today_reminders: TodayRemindersClass):
        self.today_reminders = today_reminders

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        data['today_reminders'] = self.today_reminders
        return await handler(event, data)