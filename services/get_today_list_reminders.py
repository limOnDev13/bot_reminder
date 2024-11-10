from datetime import datetime
from typing import List

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from asyncpg import Record
from asyncpg.pool import Pool

from database import (
    DataBaseClass,
    TodayRemindersClass,
    delete_irrelevant_reminders,
    get_today_reminders,
)


def plan_cron_save_today_reminders(
    scheduler: AsyncIOScheduler, pool: Pool, today_reminders: TodayRemindersClass
):
    scheduler.add_job(
        _save_list_today_reminders,
        trigger="cron",
        id="get_today_list_cron",
        hour=0,
        minute=0,
        kwargs={"pool": pool, "today_reminders": today_reminders},
    )


def plan_date_save_today_reminders(
    scheduler: AsyncIOScheduler, pool: Pool, today_reminders: TodayRemindersClass
):
    scheduler.add_job(
        _save_list_today_reminders,
        trigger="date",
        id="get_today_list_date",
        run_date=datetime.now(),
        kwargs={"pool": pool, "today_reminders": today_reminders},
    )


# Функция, которая ежедневно в 00:00 выгружает список всех заметок
# в словарь | список (пока не решил как удобнее).
async def _save_list_today_reminders(pool: Pool, today_reminders: TodayRemindersClass):
    async with pool.acquire() as connection:
        # Очистим список заметок (на всякий случай)
        today_reminders.clear()

        database: DataBaseClass = DataBaseClass(connection)
        # Удалим неактуальные заметки
        await delete_irrelevant_reminders(database)
        # Получим заметки на сегодня из базы данных
        new_rows: List[Record] = await get_today_reminders(database)
        # Добавим в хранилище сегодняшних заметок
        today_reminders.push(new_rows)

        # Проверка работы
        today_reminders.print()
