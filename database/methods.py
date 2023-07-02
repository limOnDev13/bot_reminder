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
            SET premium = excluded.premium
                num_reminders = excluded.num_reminders
        """
    await connector.execute(command, user_id, execute=True)
