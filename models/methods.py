"""
Модуль с методами для работы с б/д
"""
from models.models import DataBase
from models.statements import st_insert_new_user


async def add_new_user(user_id: str):
    await DataBase.execute(st_insert_new_user(user_id),
                           execute=True)
