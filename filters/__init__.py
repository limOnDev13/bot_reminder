"""
Пакет с кастомными фильтрами (если не хватает встроенных фильтров
самого aiogram, или если при регистрации хэндлеров в диспетчере
анонимная функция получается слишком громоздкой)
"""
from . import is_admin, language_filter
from .other_filters import InputIsDate, InputIsTime, ItIsInlineButtonWithReminder
