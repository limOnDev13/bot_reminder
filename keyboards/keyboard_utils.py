"""
Вспомогательные функции / методы, помогающие формировать клавиатуры.
"""
from aiogram.utils.keyboard import (ReplyKeyboardBuilder,
                                    KeyboardButton,
                                    ReplyKeyboardMarkup)
from lexicon import LEXICON_RU


def build_kb_with_dates() -> ReplyKeyboardMarkup:
    kb_builder: ReplyKeyboardBuilder = ReplyKeyboardBuilder()

    bt_today: KeyboardButton = KeyboardButton(text=LEXICON_RU['today_bt_text'])
    bt_tomorrow: KeyboardButton = KeyboardButton(text=LEXICON_RU['tomorrow_bt_text'])
    bt_cancel: KeyboardButton = KeyboardButton(text=LEXICON_RU['cancel_bt_text'])

    kb_builder.row(*[bt_today, bt_tomorrow, bt_cancel], width=3)
    return kb_builder.as_markup(resize_keyboard=True)

