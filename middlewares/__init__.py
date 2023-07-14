"""
Пакет, который хранит мидлвари,
т.е. программы, которые работают с апдейтами до то момента,
как они попадут в хэндлер.
"""
from .scheduler_middleware import SchedulerMiddleware
from .db_middleware import DataBaseMiddleware
from .other_middlewares import TodayRemindersMiddleware, ProviderTokenMiddleware
