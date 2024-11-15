"""
Модуль с классами, отражающими возможные состояния пользователя.
"""

from aiogram.filters.state import State, StatesGroup


class FSMReminderCreating(StatesGroup):
    fill_date = State()
    fill_time = State()


class FSMRemindersEditor(StatesGroup):
    fill_date_to_show_reminders = State()
    show_reminds = State()
    edit_reminds = State()
    show_one_reminder = State()
    edit_one_reminder = State()
    new_text = State()
    new_date = State()
    new_time = State()
