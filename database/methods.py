"""
Модуль с методами для взаимодействия с базами данных
"""
from . connection_pool import DataBaseClass
from datetime import datetime, date
from typing import List
from asyncpg import Record


async def add_new_user(connector: DataBaseClass,
                       user_id: int):
    command = \
        """
        INSERT INTO "Users"
        VALUES($1, DEFAULT, DEFAULT)
        ON CONFLICT (user_id) DO UPDATE
            SET premium = excluded.premium,
                num_reminders = excluded.num_reminders;
        """
    await connector.execute(command, user_id, execute=True)


async def add_reminder(connector: DataBaseClass,
                       user_id: int,
                       reminder_date: str,
                       reminder_time: str,
                       reminder_text: str):
    command = \
        """
        INSERT INTO "Reminders"
        VALUES(DEFAULT, $1, $2, $3, $4, $5)
        ON CONFLICT (reminder_id) DO UPDATE
            SET reminder_date = excluded.reminder_date,
                reminder_time = excluded.reminder_time,
                reminder_text = excluded.reminder_text;
        """
    await connector.execute(command, *[user_id,
                                       reminder_date,
                                       reminder_time,
                                       reminder_text,
                                       ''],
                            execute=True)


async def select_reminders(connector: DataBaseClass,
                           user_id: int, reminder_date: date | None,
                           show_all_reminders: bool = False) -> List[Record]:
    command: str
    args: List[int | date]

    if show_all_reminders:
        command = \
            """
            SELECT reminder_id, reminder_date, reminder_time, reminder_text
            FROM "Reminders"
            WHERE user_id = $1
            ORDER BY reminder_date, reminder_time;
            """
        args = [user_id]
    else:
        command = \
            """
            SELECT reminder_id, reminder_date, reminder_time, reminder_text
            FROM "Reminders"
            WHERE user_id = $1 AND reminder_date = $2
            ORDER BY reminder_date, reminder_time;
            """
        args = [user_id, reminder_date]

    request_result: List[Record] = await connector.execute(command, *args, fetch=True)
    return request_result
