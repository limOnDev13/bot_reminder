"""
Модуль с хэндлерами для просмотра и редактирования сохраненных заметок.
"""
from aiogram import Router, F
from aiogram.filters import Command, Text, StateFilter, or_f
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from datetime import date, timedelta, datetime
from asyncpg import Record
from typing import List

from keyboards import (build_kb_to_choose_date_to_show,
                       build_kb_with_reminders)
from lexicon import LEXICON_RU
from states import FSMRemindersEditor
from database import DataBaseClass, select_reminders
from filters import InputIsDate, InputIsTime


router: Router = Router()


# Обработка команды /reminders
@router.message(Command(commands=['reminders']), StateFilter(default_state))
async def process_reminders_command(message: Message, state: FSMContext):
    await message.answer(text=LEXICON_RU['reminders'],
                         reply_markup=build_kb_to_choose_date_to_show())
    await state.set_state(FSMRemindersEditor.show_reminds)


# Обработка нажатия на клавишу ОТМЕНА в состоянии просмотра или редактирования
# напоминаний
@router.callback_query(or_f(StateFilter(FSMRemindersEditor),
                            StateFilter(FSMRemindersEditor)),
                       Text(text='back_cb'))
async def process_cancel_view_reminders(callback: CallbackQuery,
                                        state: FSMContext):
    await callback.message.edit_text(text=LEXICON_RU['cancel_view_msg'])
    await state.set_state(default_state)


# Обработка нажатия на клавишу Сегодня или Завтра в состоянии просмотра напоминаний
@router.message(StateFilter(FSMRemindersEditor.show_reminds),
                Text(text=[LEXICON_RU['today_bt_text'],
                           LEXICON_RU['tomorrow_bt_text']]))
async def show_today_or_tomorrow_reminders(message: Message,
                                           database: DataBaseClass):
    # Небольшая хитрость, чтобы удалить клавиатуру с выбором дня
    await message.answer(text=LEXICON_RU['sec_please'],
                         reply_markup=ReplyKeyboardRemove())
    reminders: List[Record]
    msg_text: str
    selected_date: date

    if message.text == LEXICON_RU['today_bt_text']:
        selected_date = date.today()
        msg_text = LEXICON_RU['today_msg']
    else:
        selected_date = date.today() + timedelta(days=1)
        msg_text = LEXICON_RU['tomorrow_msg']

    reminders = await select_reminders(
        connector=database,
        user_id=message.from_user.id,
        reminder_date=selected_date
    )

    await message.answer(text=msg_text,
                         reply_markup=build_kb_with_reminders(
                             user_id=message.from_user.id,
                             reminders=reminders,
                             pos_first_elem=0,
                             with_time=True
                         ))


# Хэндлер для обработки правильно введенной (по формату) даты
@router.message(StateFilter(FSMRemindersEditor.show_reminds),
                InputIsDate())
async def show_reminders_on_chosen_date(message: Message,
                                        valid_date: bool | datetime,
                                        database: DataBaseClass):
    if valid_date:
        reminders: List[Record] = await select_reminders(
            connector=database,
            user_id=message.from_user.id,
            reminder_date=valid_date.date()
        )
        await message.answer(
            text=(LEXICON_RU['reminders_on_chosen_date_msg'] +
                  valid_date.strftime("%d.%m.%Y")),
            reply_markup=build_kb_with_reminders(
                user_id=message.from_user.id,
                reminders=reminders,
                pos_first_elem=0,
                with_time=True
            )
        )
    else:
        await message.answer(text=LEXICON_RU['past_date'])
