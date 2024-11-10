"""
Модуль, в котором реализованы специальные фильтры на ввод даты и времени
"""

from datetime import date, datetime, time
from typing import Any, List

from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message


class InputIsDate(BaseFilter):
    """
    Класс для проверки корректности ввода даты.
    """

    """
    Функция, которая сначала проверяет правильность формата ввода даты,
    после проверяет, существует ли такая дата, и прошла ли она.
    """

    async def __call__(self, message: Message) -> bool | dict[str, bool | datetime]:
        input_date: str = message.text.lstrip(" \n\t")
        input_text: List[str] = input_date.split(".")

        for item in input_text:
            if not item.isdigit():
                return False

        if len(input_text) == 3:
            entered_date = input_date
        elif len(input_text) == 2:
            entered_date = input_date + f".{date.today().year}"
        elif len(input_text) == 1:
            entered_date = (
                input_date + f".{date.today().month}" + f".{date.today().year}"
            )
        else:
            return False

        try:
            valid_date: datetime = datetime.strptime(entered_date, "%d.%m.%Y")
            if valid_date.date() < date.today():
                return {"valid_date": False}
            else:
                return {"valid_date": valid_date}
        except ValueError:
            return False


class CorrectDateToModifyReminder(BaseFilter):
    """
    Класс для проверки корректности ввода даты.
    """

    """
    Функция, которая сначала проверяет правильность формата ввода даты,
    после проверяет, существует ли такая дата, и прошла ли она.
    """

    async def __call__(
        self, message: Message, state: FSMContext
    ) -> bool | dict[str, bool | datetime]:
        input_date: str = message.text.lstrip(" \n\t")
        input_text: List[str] = input_date.split(".")

        for item in input_text:
            if not item.isdigit():
                return False

        if len(input_text) == 3:
            entered_date = input_date
        elif len(input_text) == 2:
            entered_date = input_date + f".{date.today().year}"
        elif len(input_text) == 1:
            entered_date = (
                input_date + f".{date.today().month}" + f".{date.today().year}"
            )
        else:
            return False

        try:
            reminder_info: dict[str, Any] = await state.get_data()
            reminder_time: time = reminder_info["reminder_time"]

            valid_date: datetime = datetime.strptime(entered_date, "%d.%m.%Y")
            if (valid_date.date() < date.today()) or (
                (valid_date.date() == date.today())
                and (reminder_time < datetime.now().time())
            ):
                return {"valid_date": False}
            else:
                return {"valid_date": valid_date}
        except ValueError:
            return False


class InputIsTime(BaseFilter):
    """
    Класс-фильтр для проверки валидности введенного времени
    """

    async def __call__(self, message: Message) -> bool | dict[str, bool | datetime]:
        input_time = message.text.lstrip(" \n\t")
        input_text: List[str] = input_time.split(":")

        for item in input_text:
            if not item.isdigit():
                return False

        try:
            valid_time_str = datetime.today().strftime("%Y-%m-%d") + " " + input_time
            valid_time: datetime = datetime.strptime(valid_time_str, "%Y-%m-%d %H:%M")
            current_time: datetime = datetime.now()

            if valid_time > current_time:
                return {"selected_more_current": True, "valid_time": valid_time}
            else:
                return {"selected_more_current": False, "valid_time": valid_time}
        except ValueError:
            return False


class ItIsInlineButtonWithReminder(BaseFilter):
    """
    Класс-фильтр для проверки callback, начинающийся на view
     (с таким префиксом сохраняются инлайн-кнопки с какой-нибудь заметкой)
    """

    async def __call__(self, callback: CallbackQuery) -> bool | dict[str, int]:
        cb_text: str = callback.data

        parsed_cb_text: List[str] = cb_text.split(":")

        if not parsed_cb_text[0] == "view":
            return False
        else:
            return {"reminder_id": int(parsed_cb_text[2])}


class ItIsPageNumber(BaseFilter):
    """
    Класс-фильтр для проверки callback кнопки с номером страницы в списке заметок
    """

    async def __call__(self, callback: CallbackQuery) -> bool:
        cb_text: str = callback.data

        parsed_cb_text: List[str] = cb_text.split("-")
        if (
            (len(parsed_cb_text) == 2)
            and parsed_cb_text[0].isdigit()
            and parsed_cb_text[1].isdigit()
        ):
            return True
        else:
            return False


class ItIsReminderForDeleting(BaseFilter):
    """
    Класс-фильтр для удаления напоминания при нажатии на заметку в
     списке в режиме удаления
    """

    async def __call__(self, callback: CallbackQuery) -> bool | dict[str, int]:
        cb_text: str = callback.data

        parsed_cb_text: List[str] = cb_text.split(":")

        if (
            (len(parsed_cb_text) == 3)
            and (parsed_cb_text[0] == "del")
            and (parsed_cb_text[1].isdigit())
            and (parsed_cb_text[2].isdigit())
        ):
            return {"reminder_id": int(parsed_cb_text[2])}
        else:
            return False
