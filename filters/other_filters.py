"""
Модуль, в котором реализованы специальные фильтры на ввод даты и времени
"""
from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from typing import List
from datetime import date, time, datetime


class InputIsDate(BaseFilter):
    """
    Класс для проверки корректности ввода даты.
    """
    '''
    Функция, которая сначала проверяет правильность формата ввода даты,
    после проверяет, существует ли такая дата, и прошла ли она.
    '''
    async def __call__(self, message: Message) -> bool | dict[str, bool | datetime]:
        input_date: str = message.text.lstrip(' \n\t')
        input_text: List[str] = input_date.split('.')

        for item in input_text:
            if not item.isdigit():
                return False

        if len(input_text) == 3:
            entered_date = input_date
        elif len(input_text) == 2:
            entered_date = input_date + f'.{date.today().year}'
        elif len(input_text) == 1:
            entered_date = input_date + f'.{date.today().month}' + \
                           f'.{date.today().year}'
        else:
            return False

        try:
            valid_date: datetime = datetime.strptime(entered_date, "%d.%m.%Y")
            if valid_date.date() < date.today():
                return {'valid_date': False}
            else:
                return {'valid_date': valid_date}
        except ValueError:
            return False


class InputIsTime(BaseFilter):
    """
    Класс-фильтр для проверки валидности введенного времени
    """
    async def __call__(self, message: Message) -> bool | dict[str, bool | datetime]:
        input_time = message.text.lstrip(' \n\t')
        input_text: List[str] = input_time.split(':')

        for item in input_text:
            if not item.isdigit():
                return False

        try:
            valid_time_str = datetime.today().strftime("%Y-%m-%d") + ' ' + input_time
            valid_time: datetime = datetime.strptime(valid_time_str, "%Y-%m-%d %H:%M")
            current_time: datetime = datetime.now()

            if valid_time > current_time:
                return {'selected_more_current': True,
                        'valid_time': valid_time}
            else:
                return {'selected_more_current': False,
                        'valid_time': valid_time}
        except ValueError:
            return False


class ItIsInlineButtonWithReminder(BaseFilter):
    """
    Класс-фильтр для проверки callback, начинающийся на view
     (с таким префиксом сохраняются инлайн-кнопки с какой-нибудь заметкой)
    """
    async def __call__(self, callback: CallbackQuery) -> bool | dict[str, int]:
        cb_text: str = callback.data

        parsed_cb_text: List[str] = cb_text.split(':')

        if not parsed_cb_text[0] == 'view':
            return False
        else:
            return {'reminder_id': int(parsed_cb_text[2])}
