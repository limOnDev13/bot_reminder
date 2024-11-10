"""
Модуль, в котором хранится класс для хранения списка напоминаний на сегодня
"""

from datetime import date, datetime, time
from typing import List
import logging

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from asyncpg import Record
from asyncpg.pool import Pool

from database import DataBaseClass, delete_reminder


class TodayRemindersClass:
    def __init__(self, scheduler: AsyncIOScheduler, bot: Bot, pool: Pool):
        self.scheduler: AsyncIOScheduler = scheduler
        self.bot: Bot = bot
        self.pool: Pool = pool

        self.today_reminders: List[Record] = []

    # Добавляем заметку в список запланированных сообщений
    def push(self, reminders: List[Record]):
        for reminder in reminders:

            # Проверим, что такой заметки пока не запланировано
            is_reminder_in_today_list: bool = False
            for reminder_from_list in self.today_reminders:
                if reminder_from_list["reminder_id"] == reminder["reminder_id"]:
                    is_reminder_in_today_list = True

            if not is_reminder_in_today_list:
                # Добавляем заметку в хранилище
                self.today_reminders.append(reminder)
                # Планируем отправление сообщения
                self._planning_send_reminder(reminder=reminder)

    def delete(self, reminder: Record):
        index: int = 0

        for reminder_from_list in self.today_reminders:
            if reminder_from_list["reminder_id"] == reminder["reminder_id"]:
                # Удаляем запланированное сообщение
                self.scheduler.remove_job(str(reminder["reminder_id"]))
                # Удаляем id из списка запланированных сообщений
                self.today_reminders.pop(index)
                break
            else:
                index += 1

    def print(self):
        for reminder in self.today_reminders:
            print(reminder)

    def clear(self):
        self.today_reminders.clear()

    async def _send_appropriate_reminder(self, reminder: Record):
        logging.info("Start sending reminder")
        reminder_type: str = reminder["msg_type"]
        user_id: int = reminder["user_id"]
        file_id: str = reminder["file_id"]
        reminder_text: str = reminder["reminder_text"]

        # Отправляем сообщение пользователю
        if reminder_type == "text":
            await self.bot.send_message(user_id, reminder_text)
        elif reminder_type == "photo":
            await self.bot.send_photo(user_id, photo=file_id, caption=reminder_text)
        elif reminder_type == "video":
            await self.bot.send_video(user_id, video=file_id, caption=reminder_text)
        elif reminder_type == "audio":
            await self.bot.send_audio(user_id, audio=file_id, caption=reminder_text)
        elif reminder_type == "document":
            await self.bot.send_document(
                user_id, document=file_id, caption=reminder_text
            )
        elif reminder_type == "voice":
            await self.bot.send_voice(user_id, voice=file_id)
        elif reminder_type == "video_note":
            await self.bot.send_video_note(user_id, video_note=file_id)

        # Удаляем напоминание из бд
        async with self.pool.acquire() as connection:
            database: DataBaseClass = DataBaseClass(connection)
            await delete_reminder(database, reminder["reminder_id"])

        # Удаляем напоминание из хранилища задач
        index: int = 0

        for reminder_from_list in self.today_reminders:
            if reminder_from_list["reminder_id"] == reminder["reminder_id"]:
                self.today_reminders.pop(index)
                break
            else:
                index += 1

    @staticmethod
    def _create_full_datetime(r_date: date, r_time: time):
        return datetime(
            year=r_date.year,
            month=r_date.month,
            day=r_date.day,
            hour=r_time.hour,
            minute=r_time.minute,
        )

    def _planning_send_reminder(self, reminder: Record):
        logging.debug("reminder_id is %s", str(reminder["reminder_id"]))
        self.scheduler.add_job(
            self._send_appropriate_reminder,
            trigger="date",
            id=str(reminder["reminder_id"]),
            run_date=self._create_full_datetime(
                r_date=reminder["reminder_date"], r_time=reminder["reminder_time"]
            ),
            kwargs={"reminder": reminder},
        )
