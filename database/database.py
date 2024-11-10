"""The module responsible for connecting to the database."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config_data import Config, load_config

config: Config = load_config()
DB_URL: str = (
    f"postgresql+asyncpg://{config.con_pool.user.user}:"
    f"{config.con_pool.user.password}@{config.con_pool.db.host}:5432"
)

engine = create_async_engine(DB_URL)
Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    """Declarative base class."""

    pass
