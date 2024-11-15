"""
Модуль с мидлварью, отвечающей за контроль за количеством
 заметок и типов заметок для НЕ премиум пользователей
"""

from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.types import Message
from aiogram.types.message import ContentType
from asyncpg import Record
from asyncpg.pool import Pool

from database import DataBaseClass
from database.methods import check_premium, get_num_reminders
from lexicon import LEXICON_RU

MAX_NUM_REMINDERS_FOR_NOT_PREMIUM: int = 50


class RemindersLimits(BaseMiddleware):
    def __init__(self, pool: Pool):
        super().__init__()
        self.pool: Pool = pool

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        async with self.pool.acquire() as connection:
            # Создадим объект класса для работы с бд
            database: DataBaseClass = DataBaseClass(connection)

            # Получим статус пользователя
            is_premium_query_result: Record = await check_premium(
                connector=database, user_id=event.from_user.id
            )
            if is_premium_query_result is None:
                # Новый юзер - пропускаем апдейт.
                return await handler(event, data)

            is_premium: bool = is_premium_query_result["premium"]

            # Если не премиум
            if is_premium is False:
                # Получим количество
                num_reminders_query_result: Record = await get_num_reminders(
                    connector=database, user_id=event.from_user.id
                )
                num_reminders: int = num_reminders_query_result["num_reminders"]

                # Если количество заметок превышает лимит для не премиум пользователей
                if num_reminders >= MAX_NUM_REMINDERS_FOR_NOT_PREMIUM:
                    # Сообщим пользователю, что он исчерпал лимит
                    await event.answer(text=LEXICON_RU["exceeding_limit_on_reminders"])
                else:
                    # Если пользователь прислал только текст
                    if event.content_type in {ContentType.TEXT}:
                        return await handler(event, data)
                    # Если не премиум пользователь прислал что-то другое
                    else:
                        # Сообщим пользователю,
                        # что не премиумы могут сохранять только текстовые напоминания
                        await event.answer(text=LEXICON_RU["not_text_from_not_premium"])
            # Если премиум или новый юзер (is_premium == None)
            else:
                # Пропускаем апдейт
                return await handler(event, data)
