"""
Пакет с модулями для реализации какой-то бизнес-логики бота.
"""
from . import services
from .execution_planning import planning_get_today_reminders,\
    planning_send_appropriate_reminder
