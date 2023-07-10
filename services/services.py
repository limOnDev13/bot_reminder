"""
Модуль с реализацией бизнес-логики.
"""
import asyncio
from aiogram import Bot
from asyncpg.pool import Pool
from asyncpg import Record
from typing import List

from database import DataBaseClass, get_today_reminders, TodayRemindersClass


# Функция, которая ежедневно в 00:00 выгружает список всех заметок
# в словарь | список (пока не решил как удобнее).
async def save_list_today_reminders(pool: Pool,
                                    today_reminders: List[Record]):
    async with pool.acquire() as connection:
        # Очистим список заметок (на всякий случай)
        today_reminders.clear()
        # Получим заметки на сегодня из базы данных
        database: DataBaseClass = DataBaseClass(connection)
        new_rows: List[Record] = await get_today_reminders(database)
        # Добавим в хранилище сегодняшних заметок
        today_reminders.push(rows=new_rows)


# Функция, которая при наступлении назначенного времени отправляет
# соответствующую заметку и удаляет ее из бд и оперативной памяти
async def send_appropriate_reminder(bot: Bot, pool: Pool,
                                    today_reminders_list: TodayRemindersClass):
    showed_reminders: List[Record] = await today_reminders_list.pop(pool=pool)
    tasks_to_show_reminders = [bot.send_message(reminder['user_id'],
                                                reminder['reminder_text'])
                               for reminder in showed_reminders]
    await asyncio.gather(*tasks_to_show_reminders)
