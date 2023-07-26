"""
Модуль с методами для взаимодействия с базами данных
"""
from . connection_pool import DataBaseClass
from datetime import date, time, datetime
from typing import List, Tuple
from asyncpg import Record


# Добавим в таблицу Users нового пользователя
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


# Добавим в таблицу Reminders новую заметку
async def add_reminder(connector: DataBaseClass,
                       user_id: int,
                       reminder_date: date,
                       reminder_time: time,
                       reminder_text: str) -> Record:
    # Добавим заметку в базу данных
    command1 = \
        """
        INSERT INTO "Reminders"
        VALUES(DEFAULT, $1, $2, $3, $4, $5, $6)
        ON CONFLICT (reminder_id) DO UPDATE
            SET reminder_date = excluded.reminder_date,
                reminder_time = excluded.reminder_time,
                reminder_text = excluded.reminder_text;
        """
    await connector.execute(command1, *[user_id, reminder_date,
                                        reminder_time, reminder_text,
                                        '', True],
                            execute=True)
    # Получим последнюю заметку
    command2 = \
        """
        SELECT * FROM "Reminders"
        WHERE last_reminder = True
        """
    result_reminder = await connector.execute(command2, fetchrow=True)
    # Изменим у последней заметки параметр last_reminder на False
    command3 = \
        """
        UPDATE "Reminders"
        SET last_reminder = False
        WHERE last_reminder = True;
        """
    await connector.execute(command3, execute=True)

    return result_reminder


# Выберем в таблице Reminders заметки на выбранную дату или все заметки
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


# Выберем в таблице Reminders определенную заметку
async def select_chosen_reminder(connector: DataBaseClass, reminder_id: int) -> Record:
    command: str = \
        """
        SELECT *
        FROM "Reminders"
        WHERE reminder_id = $1
        """
    return await connector.execute(command, reminder_id, fetchrow=True)


# Удалим в таблице Reminders определенную заметку
async def delete_reminder(connector: DataBaseClass, reminder_id: int) -> None:
    command = \
        """
        DELETE FROM "Reminders"
        WHERE reminder_id = $1;
        """
    await connector.execute(command, reminder_id, execute=True)


# Обновим в таблице Reminders в определенной заметке текст
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


# Обновим в таблице Reminders в определенной заметке дату
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


# Обновим в таблице Reminders в определенной заметке время
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


# Выберем в таблице Reminders все (полные) заметки определенного пользователя
async def show_all_reminders(connector: DataBaseClass,
                             user_id: int) -> List[Record]:
    command = \
        """
        SELECT * FROM "Reminders"
        WHERE user_id = $1
        ORDER BY reminder_date, reminder_time
        """
    return await connector.execute(command, user_id, fetch=True)


# Выберем в таблице Reminders заметки всех пользователей на сегодняшний день
async def get_today_reminders(connector: DataBaseClass) -> List[Record]:
    command = \
        """
        SELECT * FROM "Reminders"
        WHERE reminder_date = $1
        ORDER BY reminder_time
        """
    return await connector.execute(command, date.today(), fetch=True)


# Удалим из таблицы Reminders несколько заметок
async def delete_some_reminders(connector: DataBaseClass,
                               input_data: List[Tuple[int]]) -> None:
    command = \
        """
        DELETE FROM "Reminders"
        WHERE reminder_id = $1;
        """
    await connector.executemany(command, input_data)


# Удалим неактуальные заметки
async def delete_irrelevant_reminders(connector: DataBaseClass):
    command = \
        """
        DELETE FROM "Reminders"
        WHERE (reminder_time < $1 AND reminder_date = $2) 
        OR (reminder_date < $2);
        """
    await connector.execute(command, *[datetime.now().time(), date.today()],
                            execute=True)


# Изменим премиум-статус пользователя
async def set_premium(connector: DataBaseClass, user_id: int):
    command = \
        """
        Update "Users"
        SET premium = True
        WHERE user_id = $1
        """
    await connector.execute(command, user_id, execute=True)


# Проверим премиум-статус пользователя
async def check_premium(connector: DataBaseClass, user_id: int) -> Record:
    command = \
        """
        SELECT premium FROM "Users"
        WHERE user_id = $1
        """
    return await connector.execute(command, user_id, fetchrow=True)


# Получаем количество заметок
async def get_num_reminders(connector: DataBaseClass, user_id: int) -> Record:
    # Сначала обновим информацию о количестве, а после уже получим значение
    command = \
        """
        UPDATE "Users"
        SET num_reminders = (SELECT COUNT(*) FROM "Reminders" WHERE user_id = $1)
        WHERE user_id = $1;
        """
    await connector.execute(command, user_id, execute=True)

    command = \
        """
        SELECT num_reminders FROM "Users"
        WHERE user_id = $1;
        """
    return await connector.execute(command, user_id, fetchrow=True)

