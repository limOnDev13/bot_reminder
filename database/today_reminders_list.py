"""
Модуль, в котором хранится класс для хранения списка напоминаний на сегодня
"""
from typing import List, Tuple
from asyncpg import Record
from datetime import time, date, datetime
from asyncpg.pool import Pool
from apscheduler.job import Job
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from datetime import datetime, timedelta

from database import DataBaseClass, delete_some_reminders
from services import services

class TodayRemindersClass:
    """
    Класс для хранения напоминаний на сегодняшний день.
    Представлен в виде стека, только при добавлении новых напоминаний на сегодня
    в течение сегодняшнего дня (сегодня добавили заметку на сегодня) стек будет
    сортироваться по времени.
    """
    def __init__(self):
        self.today_reminders: List[Record] = []
        self.count: int = 0
        self.near_time: time = time(hour=0, minute=0)
        self.number_near_reminders: int = 0

    # Рассчитаем информацию о ближайших напоминаниях
    def _find_near_reminders(self):
        self.near_time = self.today_reminders[-1]['reminder_time']
        self.number_near_reminders = 0

        for reminder in self.today_reminders[::-1]:
            if reminder['reminder_time'] == self.near_time:
                self.number_near_reminders += 1
            else:
                break

    # Добавляем элементы в стек и сортируем обновленный список
    # (схема: сначала добавляем в базу данных, потом в оперативную память, в конце
    # в список сегодняшних заметок)
    def push(self, rows: Record):
        # Добавляем новые строки
        self.today_reminders += rows
        self.count += len(rows)
        # Сортируем
        self.today_reminders.sort(key=lambda d: d['reminder_time'])
        # Обновляем информацию о ближайших заметках
        self._find_near_reminders()

    # Извлекаем последние заметки с одинаковым временем
    # (схема: удаляем сначала из хранилища сегодняшних заметок, потом из базы данных)
    async def pop(self, pool: Pool) -> List[Record]:
        # Если количество всех заметок на сегодня не меньше
        # количества ближайших заметок
        if self.count >= self.number_near_reminders:
            result_reminders: List[Record] = []  # Список удаляемых заметок
            deleted_reminders_id: List[Tuple[int]] = []  # Список удаляемых id

            # Извлекаем ближайшие заметки
            for _ in range(self.number_near_reminders):
                deleted_reminder: Record = self.today_reminders.pop()

                deleted_reminders_id.append((deleted_reminder['reminder_id']))
                result_reminders.append(deleted_reminder)
            self.count -= self.number_near_reminders

            # Удалим выбранные заметки из базы данных
            async with pool.acquire() as connection:
                database: DataBaseClass = DataBaseClass(connection)
                await delete_some_reminders(database, deleted_reminders_id)

            # Обновим информацию о ближайших заметках
            self._find_near_reminders()

            return result_reminders
        else:
            print('Список сегодняшних заметок пустой.')

    # Удаляем заметку по reminder_id
    # (схема: сначала удаляем из базы данных, потом из оперативной памяти, в конце
    # из списка сегодняшних заметок)
    def delete(self, reminder_on_deletion_id: int):
        index: int = 0
        # Найдем необходимую заметку
        for reminder in self.today_reminders:
            if reminder['reminder_id'] == reminder_on_deletion_id:
                self.today_reminders.pop(index)
                break
            else:
                index += 1
        # Если индекс меньше длины массива
        if index < len(self.today_reminders):
            # в списке была такая заметка, поэтому обновим информацию
            # о ближайших заметках
            self._find_near_reminders()

    # Вернем полную ближайшую дату - время
    def get_near_datetime(self) -> datetime:
        result_datetime: datetime = datetime(year=date.today().year,
                                             month=date.today().month,
                                             day=date.today().day,
                                             hour=self.near_time.hour,
                                             minute=self.near_time.minute)
        return result_datetime

    # Очищаем весь список
    def clear(self):
        self.today_reminders.clear()
        self.count = 0


class TodayRemindersClass2:
    def __init__(self, scheduler: AsyncIOScheduler, bot: Bot, pool: Pool):
        self.scheduler: AsyncIOScheduler = scheduler
        self.bot: Bot = bot
        self.pool: Pool = pool

        self.today_reminders: List[Record] = []
        self.count: int = 0
        self.jobs_ids_with_reminders_ids: dict[int, Job]

    def push(self, rows: List[Record]):
        self.today_reminders += rows

    def pop(self, reminder_id: int):
        index: int = 0

        for reminder in self.today_reminders:
            if reminder['reminder_id'] == reminder_id:
                self.today_reminders.pop(index)
                break
            else:
                index += 1

    def _planning_to_send_reminder(self) -> Job:
        pass

