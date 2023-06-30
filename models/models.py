"""
Модуль с ORM-моделями б/д.
"""
import asyncpg
from asyncpg.pool import Pool
from asyncpg import Connection

from typing import Union


class DataBaseClass:
    def __init__(self):
        self.pool: Union[Pool | None] = None

    async def create_pool(self):
        self.pool = await asyncpg.create_pool(

        )

    async def execute(self, statement: str,
                      fetch: bool = False,
                      fetchval: bool = False,
                      fetchrow: bool = False,
                      execute: bool = False):
        async with self.pool.acquire() as connection:
            connection: Connection
            async with connection.transaction():
                if fetch:
                    result = await connection.fetch(statement)
                elif fetchval:
                    result = await connection.fetchval(statement)
                elif fetchrow:
                    result = await connection.fetchrow(statement)
                elif execute:
                    result = await connection.execute(statement)
        return result


DataBase: DataBaseClass = DataBaseClass()
