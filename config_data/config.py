"""
Файл с конфигурационными данными для бота, б/д, сторонних сервисов и т.п.
"""
from dataclasses import dataclass
from environs import Env


@dataclass
class TgBot:
    token: str            # Токен для доступа к телеграм-боту
    admin_ids: list[int]


@dataclass
class UserDB:
    user: str
    password: str


@dataclass
class DB:
    host: str
    port: int
    db_name: str


@dataclass
class ConnectionsPool:
    db: DB
    user: UserDB
    min_size: int
    max_size: int


@dataclass
class Config:
    tg_bot: TgBot
    con_pool: ConnectionsPool


def load_config(path: str | None = None) -> Config:
    env = Env()
    env.read_env(path)
    return Config(tg_bot=TgBot(token=env('BOT_TOKEN'),
                               admin_ids=list(map(int, env.list('ADMIN_IDS')))),
                  con_pool=ConnectionsPool(db=DB(host=env('HOST'),
                                                 port=int(env('PORT')),
                                                 db_name=env('DATABASE')),
                                           user=UserDB(user=env('USER'),
                                                       password=env('PASSWORD')),
                                           min_size=int(env('POOL_MIN_SIZE')),
                                           max_size=int(env('POOL_MAX_SIZE'))))
