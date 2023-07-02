"""
Модуль, для создания и хранения пула подключения в классе
"""
from asyncpg.pool import Pool
from asyncpg import Connection


class DataBaseClass:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def execute(self, command: str, *args,
                      fetch: bool = False,
                      fetchval: bool = False,
                      fetchrow: bool = False,
                      execute: bool = False):
        if fetch:
            return await self.pool.fetch(command, *args)
        elif fetchval:
            return await self.pool.fetchval(command, *args)
        elif fetchrow:
            return await self.pool.fetchrow(command, *args)
        elif execute:
            return await self.pool.execute(command, *args)
