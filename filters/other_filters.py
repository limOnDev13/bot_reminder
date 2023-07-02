"""
Модуль, в котором реализованы специальные фильтры на ввод даты и времени
"""
from aiogram.filters import BaseFilter
from aiogram.types import Message

from typing import List, Union
from datetime import date


class InputIsDate(BaseFilter):
    """
    Класс для проверки корректности ввода даты.
    """
    @staticmethod
    def _try_check_entered_date(day: int, month: int, year: int) -> bool | dict[str, bool | str]:
        try:
            entered_date = date(year, month, day)
            if entered_date < date.today():
                return {'valid_date': False}
            else:
                result_date = str(year) + '-' + str(month) + '-' + str(day)
                return {'valid_date': result_date}
        except:
            return False

    '''
    Функция, которая сначала проверяет правильность формата ввода даты,
    после проверяет, существует ли такая дата, и прошла ли она.
    '''
    async def __call__(self, message: Message) -> bool | dict[str, bool | str]:
        input_text: List[str] = message.text.lstrip(' \n\t').split('.')
        int_text: List[int] = []

        for item in input_text:
            if not item.isdigit():
                return False
            else:
                int_text.append(int(item))
        print(int_text)

        if len(int_text) == 3:
            result = self._try_check_entered_date(int_text[0], int_text[1], int_text[2])
        elif len(int_text) == 2:
            result = self._try_check_entered_date(int_text[0], int_text[1], date.today().year)
        elif len(int_text) == 1:
            result = self._try_check_entered_date(int_text[0], date.today().month, date.today().year)
        else:
            return False

        return result
