"""
Модуль, в котором хранится класс для хранения списка напоминаний на сегодня
"""
from typing import List
from asyncpg import Record
from datetime import time, date, datetime
from asyncpg.pool import Pool
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot

from database import DataBaseClass, delete_reminder


class TodayRemindersClass:
    def __init__(self, scheduler: AsyncIOScheduler, bot: Bot, pool: Pool):
        self.scheduler: AsyncIOScheduler = scheduler
        self.bot: Bot = bot
        self.pool: Pool = pool

        self.today_reminders: List[Record] = []

    # Добавляем заметку в список запланированных сообщений
    def push(self, reminders: List[Record]):

        print(f'reminders = {reminders}')

        for reminder in reminders:

            print(f'reminder = {reminder}')

            # Проверим, что такой заметки пока не запланировано
            is_reminder_in_today_list: bool = False
            for reminder_from_list in self.today_reminders:
                if reminder_from_list['reminder_id'] == reminder['reminder_id']:
                    is_reminder_in_today_list = True

            if not is_reminder_in_today_list:
                # Добавляем заметку в хранилище
                self.today_reminders.append(reminder)
                # Планируем отправление сообщения
                self._planning_send_reminder(reminder=reminder)

    def delete(self, reminder: Record):
        index: int = 0

        for reminder_from_list in self.today_reminders:
            if reminder_from_list['reminder_id'] == reminder['reminder_id']:
                # Удаляем запланированное сообщение
                self.scheduler.remove_job(str(reminder['reminder_id']))
                # Удаляем id из списка запланированных сообщений
                self.today_reminders.pop(index)
                break
            else:
                index += 1

    def edit_reminder(self, reminder_id: int,
                      new_text: bool | str = False,
                      new_time: bool | time = False):
        for reminder in self.today_reminders:
            # Если в списке заметок есть полученная заметка
            if reminder_id == reminder['reminder_id']:
                # Если ввели новый текст
                if new_text:
                    reminder['reminder_text'] = new_text
                # Если ввели новое время
                elif new_time:
                    reminder['reminder_time'] = new_time
                # Изменим запланированную отправку сообщения
                self._modify_planned_send_reminder(reminder=reminder)
                # Выйдем из цикла
                break

    def print(self):
        for reminder in self.today_reminders:
            print(reminder)

    def clear(self):
        self.today_reminders.clear()

    async def _send_appropriate_reminder(self, reminder):
        # Отправляем сообщение пользователю
        await self.bot.send_message(reminder['user_id'], reminder['reminder_text'])

        # Удаляем напоминание из бд
        async with self.pool.acquire() as connection:
            database: DataBaseClass = DataBaseClass(connection)
            await delete_reminder(database, reminder['reminder_id'])

        # Удаляем напоминание из хранилища задач
        index: int = 0

        for reminder_from_list in self.today_reminders:
            if reminder_from_list['reminder_id'] == reminder['reminder_id']:
                self.today_reminders.pop(index)
                break
            else:
                index += 1

    @staticmethod
    def _create_full_datetime(r_date: date, r_time: time):
        return datetime(year=r_date.year, month=r_date.month, day=r_date.day,
                        hour=r_time.hour, minute=r_time.minute)

    def _planning_send_reminder(self, reminder: Record):
        self.scheduler.add_job(
            self._send_appropriate_reminder, trigger='date',
            id=str(reminder['reminder_id']),
            run_date=self._create_full_datetime(r_date=reminder['reminder_date'],
                                                r_time=reminder['reminder_time']),
            kwargs={'reminder': reminder})

    def _modify_planned_send_reminder(self, reminder: Record):
        self.scheduler.modify_job(job_id=str(reminder['reminder_id']),
                                  kwargs={'reminder': reminder})
