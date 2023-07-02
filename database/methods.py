"""
Модуль с методами для взаимодействия с базами данных
"""
from . connection_pool import DataBaseClass


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
                       reminder_id: int,
                       user_id: int,
                       reminder_date: str,
                       reminder_time: str,
                       reminder_text: str):
    command = \
        """
        INSERT INTO "Reminders"
        VALUES($1, $2, $3, $4, $5, none)
        ON CONFLICT (reminder_id, user_id) DO UPDATE
            SET reminder_date = excluded.reminder_date,
                reminder_time = excluded.reminder_time,
                reminder_text = excluded.reminder_text;
        """
    await connector.execute(command,
                            *[reminder_id,
                              user_id,
                              reminder_date,
                              reminder_time,
                              reminder_text],
                            execute=True)

