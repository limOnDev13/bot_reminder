"""
Модуль с классами, отражающими возможные состояния пользователя.
"""
from aiogram.filters.state import StatesGroup, State


class FSMReminderCreating(StatesGroup):
    fill_date = State()
    fill_time = State()
