"""
Модуль с методами для взаимодействия с базами данных
"""
from . connection_pool import DataBaseClass
from datetime import date, time
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


async def select_chosen_reminder(connector: DataBaseClass, reminder_id: int) -> Record:
    command: str = \
        """
        SELECT reminder_date, reminder_time, reminder_text
        FROM "Reminders"
        WHERE reminder_id = $1
        """
    return await connector.execute(command, reminder_id, fetchrow=True)


async def delete_reminder(connector: DataBaseClass, reminder_id: int) -> None:
    command = \
        """
        DELETE FROM "Reminders"
        WHERE reminder_id = $1;
        """
    await connector.execute(command, reminder_id, execute=True)


async def update_reminder_text(connector: DataBaseClass,
                               reminder_id: int,
                               new_reminder_text: str) -> None:
    command = \
        """
        UPDATE "Reminders"
        SET reminder_text = $1
        WHERE reminder_id = $2;
        """
    await connector.execute(command, *[new_reminder_text, reminder_id],
                            execute=True)


async def update_reminder_date(connector: DataBaseClass,
                               reminder_id: int,
                               new_reminder_date: date) -> None:
    command = \
        """
        UPDATE "Reminders"
        SET reminder_date = $1
        WHERE reminder_id = $2;
        """
    await connector.execute(command, *[new_reminder_date, reminder_id],
                            execute=True)


async def update_reminder_time(connector: DataBaseClass,
                               reminder_id: int,
                               new_reminder_time: time):
    command = \
        """
        UPDATE "Reminders"
        SET reminder_time = $1
        WHERE reminder_id = $2
        """
    await connector.execute(command, *[new_reminder_time, reminder_id],
                            execute=True)


async def show_all_reminders(connector: DataBaseClass,
                             user_id: int) -> List[Record]:
    command = \
        """
        SELECT * FROM "Reminders"
        WHERE user_id = $1
        ORDER BY reminder_date, reminder_time
        """
    return await connector.execute(command, user_id, fetch=True)
