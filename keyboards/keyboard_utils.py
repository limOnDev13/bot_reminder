"""
Вспомогательные функции / методы, помогающие формировать клавиатуры.
"""
from aiogram.utils.keyboard import (ReplyKeyboardBuilder,
                                    KeyboardButton,
                                    ReplyKeyboardMarkup,
                                    InlineKeyboardBuilder)
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from asyncpg import Record
from typing import List
from datetime import time, date, datetime

from lexicon import LEXICON_RU


def build_kb_with_dates() -> ReplyKeyboardMarkup:
    kb_builder: ReplyKeyboardBuilder = ReplyKeyboardBuilder()

    bt_today: KeyboardButton = KeyboardButton(text=LEXICON_RU['today_bt_text'])
    bt_tomorrow: KeyboardButton = KeyboardButton(text=LEXICON_RU['tomorrow_bt_text'])
    bt_cancel: KeyboardButton = KeyboardButton(text=LEXICON_RU['cancel_bt_text'])

    kb_builder.row(*[bt_today, bt_tomorrow, bt_cancel], width=3)
    return kb_builder.as_markup(resize_keyboard=True)


def build_kb_with_one_cancel() -> ReplyKeyboardMarkup:
    kb_builder: ReplyKeyboardBuilder = ReplyKeyboardBuilder()

    bt_cancel: KeyboardButton = KeyboardButton(text=LEXICON_RU['cancel_bt_text'])

    kb_builder.row(*[bt_cancel], width=1)
    return kb_builder.as_markup(resize_keyboard=True)


def build_kb_to_choose_date_to_show() -> ReplyKeyboardMarkup:
    kb_builder: ReplyKeyboardBuilder = ReplyKeyboardBuilder()

    bt_today: KeyboardButton = KeyboardButton(text=LEXICON_RU['today_bt_text'])
    bt_tomorrow: KeyboardButton = KeyboardButton(text=LEXICON_RU['tomorrow_bt_text'])
    bt_all: KeyboardButton = KeyboardButton(text=LEXICON_RU['all'])
    bt_cancel: KeyboardButton = KeyboardButton(text=LEXICON_RU['cancel_bt_text'])

    kb_builder.row(*[bt_today, bt_tomorrow, bt_all, bt_cancel], width=3)
    return kb_builder.as_markup(resize_keyboard=True)


class RemindersCallbackFactory(CallbackData, prefix='view'):
    user_id: int
    reminder_id: int


# Билдер клавиатуры для просмотра списка заметок на выбранную дату
# (или для просмотра всех заметок)
def build_kb_with_reminders(user_id: int,
                            reminders: List[Record],
                            pos_first_elem: int,
                            page_size: int = 10,
                            with_data: bool = False,
                            with_time: bool = False) -> InlineKeyboardMarkup:
    kb_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()

    # Соберем кнопки с самими заметками. Если было указано конкретная дата,
    # то на кнопках будут указаны их время. Если нужно вывести все заметки,
    # то будут указаны даты
    buttons_with_reminders: List[InlineKeyboardButton] = []
    limit = pos_first_elem + page_size
    if len(reminders) < limit:
        limit = len(reminders)

    for num in range(pos_first_elem, limit):
        button_text: str = ''
        if with_data:
            reminder_date: date = reminders[num]['reminder_date']
            button_text += reminder_date.strftime("%d.%m.%Y") + ' '
        if with_time:
            reminder_time: time = reminders[num]['reminder_time']
            button_text += reminder_time.strftime("%H:%M") + ' '

        button_text += reminders[num]['reminder_text'][:100]

        button: InlineKeyboardButton = InlineKeyboardButton(
            text=button_text,
            callback_data=RemindersCallbackFactory(
                user_id=user_id,
                reminder_id=reminders[num]['reminder_id']
            ).pack()
        )

        buttons_with_reminders.append(button)

    # Теперь создадим кнопки для навигации по списку
    bt_previous_page: InlineKeyboardButton = InlineKeyboardButton(
        text=LEXICON_RU['previous_page'],
        callback_data=LEXICON_RU['edit_cb']
    )
    bt_next_page: InlineKeyboardButton = InlineKeyboardButton(
        text=LEXICON_RU['next_page'],
        callback_data=LEXICON_RU['edit_cb']
    )
    bt_number_showed_reminders: InlineKeyboardButton = InlineKeyboardButton(
        text=str(pos_first_elem) + ' - ' + str(limit),
        callback_data=str(pos_first_elem) + ' - ' + str(limit)
    )

    # Последние кнопки - кнопки РЕДАКТИРОВАТЬ и УДАЛИТЬ
    bt_edit: InlineKeyboardButton = InlineKeyboardButton(
        text=LEXICON_RU['edit'],
        callback_data=LEXICON_RU['edit_cb']
    )
    bt_cancel: InlineKeyboardButton = InlineKeyboardButton(
        text=LEXICON_RU['back_msg'],
        callback_data=LEXICON_RU['back_cb']
    )

    kb_builder.row(*buttons_with_reminders, width=1)
    kb_builder.row(*[bt_previous_page, bt_number_showed_reminders, bt_next_page],
                   width=3)
    kb_builder.row(*[bt_edit, bt_cancel], width=2)

    return kb_builder.as_markup(resize_keyboard=True)
