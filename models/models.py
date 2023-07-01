"""
Модуль с ORM-моделями б/д.
"""
from asyncpg.pool import Pool
from asyncpg import Connection


class DataBaseClass:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def execute(self, command: str, *args,
                      fetch: bool,
                      fetchval: bool,
                      fetchrow: bool,
                      execute: bool):
        async with self.pool.acquire() as connection:
            connection: Connection
            async with connection.transaction():
                if fetch:
                    return await connection.fetch(command, *args)
                elif fetchval:
                    return await connection.fetchval(command, *args)
                elif fetchrow:
                    return await connection.fetchrow(command, *args)
                elif execute:
                    return await connection.execute(command, *args)


