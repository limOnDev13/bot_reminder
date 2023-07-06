"""
Модуль с хэндлерами, которые отвечают за работу бота при редактировании
 одного напоминания
"""
from aiogram import Router
from aiogram.filters import Command, Text, StateFilter, or_f
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from datetime import date, timedelta, datetime, time
from asyncpg import Record
from typing import List, Any

from keyboards import (build_kb_to_choose_date_to_show, build_kb_with_reminders,
                       build_kb_with_reminder, build_kb_to_edit_one_reminder,
                       kb_with_cancel_button)
from lexicon import LEXICON_RU
from states import FSMRemindersEditor
from database import (DataBaseClass, select_reminders, select_chosen_reminder,
                      delete_reminder, update_reminder_text, update_reminder_date,
                      update_reminder_time, show_all_reminders)
from filters import (InputIsDate, ItIsInlineButtonWithReminder, InputIsTime,
                     ItIsPageNumber)
from utils import assemble_full_reminder_text


router: Router = Router()


# Хэндлер, реагирующий на нажатие кнопки Текст в режиме редактирования
@router.callback_query(StateFilter(FSMRemindersEditor.edit_one_reminder),
                       Text(text=LEXICON_RU['change_text_cb']))
async def process_edit_reminder_text(callback: CallbackQuery,
                                     state: FSMContext):
    # Установим состояние ввода нового текста
    await state.set_state(FSMRemindersEditor.new_text)
    # Отправим пользователю просьбу ввести новый текст заметки
    await callback.message.edit_text(text=LEXICON_RU['new_reminder_text'],
                                     reply_markup=kb_with_cancel_button())
    await callback.answer()


# Хэндлер, который сохраняет отредактированный текст в заметку
@router.message(StateFilter(FSMRemindersEditor.new_text))
async def process_enter_new_text(message: Message,
                                 state: FSMContext,
                                 database: DataBaseClass):
    # Обновим базу данных
    reminder_info = await state.get_data()

    await update_reminder_text(database,
                               reminder_info['reminder_id'], message.text)

    # Обновим информацию в оперативной памяти
    await state.update_data(reminder_text=message.text)

    # Покажем обновленную заметку и спросим что еще нужно изменить
    reminder_date = reminder_info['reminder_date']
    reminder_time = reminder_info['reminder_time']

    await message.answer(text=assemble_full_reminder_text(message.text,
                                                          reminder_date,
                                                          reminder_time) +
                              LEXICON_RU['done'] + LEXICON_RU['what_edit'],
                         reply_markup=build_kb_to_edit_one_reminder())

    # Перейдем обратно в режим редактирования одной заметки
    await state.set_state(FSMRemindersEditor.edit_one_reminder)


# Хэндлер, реагирующий на нажатие кнопки Дату
@router.callback_query(StateFilter(FSMRemindersEditor.edit_one_reminder),
                       Text(text=LEXICON_RU['change_date_cb']))
async def process_edit_reminder_date(callback: CallbackQuery,
                                     state: FSMContext):
    # Изменим состояние на ввод новой даты
    await state.set_state(FSMRemindersEditor.new_date)

    # Попросим ввести валидную дату
    await callback.message.edit_text(text=LEXICON_RU['new_reminder_date'],
                                     reply_markup=kb_with_cancel_button())
    await callback.answer()


# Обработка ввода даты в правильном формате
@router.message(StateFilter(FSMRemindersEditor.new_date), InputIsDate())
async def process_enter_new_date(message: Message,
                                 database: DataBaseClass,
                                 state: FSMContext,
                                 valid_date: bool | datetime):
    # Если пользователь прислал валидную дату, которая ЕЩЕ НЕ прошла
    if valid_date:
        # Обновим информацию в базе данных
        reminder_info = await state.get_data()
        await update_reminder_date(database,
                                   reminder_info['reminder_id'],
                                   valid_date.date())

        # Обновим информацию в оперативной памяти
        await state.update_data(reminder_date=valid_date.date())

        # Отправим пользователю обновленную заметку и спросим, что еще нужно изменить
        reminder_text = reminder_info['reminder_text']
        reminder_time = reminder_info['reminder_time']

        await message.answer(text=assemble_full_reminder_text(reminder_text,
                                                              valid_date.date(),
                                                              reminder_time) +
                                  LEXICON_RU['done'] + LEXICON_RU['what_edit'],
                             reply_markup=build_kb_to_edit_one_reminder())

        # Изменим состояние на редактирование одной заметки
        await state.set_state(FSMRemindersEditor.edit_one_reminder)
    # Если пользователь прислал валидную дату, которая УЖЕ прошла
    else:
        # Сообщаем пользователю, что дата уже прошла и нужно ввести корректную дату
        await message.answer(text=LEXICON_RU['past_date'],
                             reply_markup=kb_with_cancel_button())


# Хэндлер, реагирующий на нажатие кнопки Время
@router.callback_query(StateFilter(FSMRemindersEditor.edit_one_reminder),
                       Text(text=LEXICON_RU['change_time_cb']))
async def process_edit_reminder_time(callback: CallbackQuery,
                                     state: FSMContext):
    # Меняем состояние на ввод нового времени
    await state.set_state(FSMRemindersEditor.new_time)

    # Просим пользователя ввести новое время
    await callback.message.edit_text(text=LEXICON_RU['new_reminder_time'],
                                     reply_markup=kb_with_cancel_button())
    await callback.answer()


# Хэндлер, реагирующий на правильно (по формату) введенное время
@router.message(StateFilter(FSMRemindersEditor.new_time), InputIsTime())
async def process_enter_new_date(message: Message,
                                 database: DataBaseClass,
                                 state: FSMContext,
                                 selected_more_current: bool,
                                 valid_time: datetime):
    # Получим информацию о заметке из оперативной памяти
    reminder_info = await state.get_data()
    reminder_text: str = reminder_info['reminder_text']
    reminder_date: date = reminder_info['reminder_date']

    # Если пользователь выбрал сегодняшний день и ввел время, которое больше чем
    # текущее (сегодня еще не прошло), или любой другой день
    if (reminder_date == date.today()) and selected_more_current:
        # Обновим информацию в базе данных
        await update_reminder_time(database,
                                   reminder_info['reminder_id'],
                                   valid_time.time())

        # Обновим информацию в оперативной памяти
        await state.update_data(reminder_time=valid_time.time())

        # Покажем пользователю обновленную заметку и спросим, что еще нужно изменить
        await message.answer(text=assemble_full_reminder_text(reminder_text,
                                                              reminder_date,
                                                              valid_time.time()) +
                                  LEXICON_RU['done'] + LEXICON_RU['what_edit'],
                             reply_markup=build_kb_to_edit_one_reminder())

        # Изменим состояние на редактирование одной заметки
        await state.set_state(FSMRemindersEditor.edit_one_reminder)
    # Если пользователь выбрал сегодняшнюю дату и время, которое прошло
    else:
        # Сообщаем пользователю, что он выбрал время, которое сегодня уже прошло,
        # и просим ввести корректное время
        await message.answer(text=LEXICON_RU['past_time'],
                             reply_markup=kb_with_cancel_button())


# Хэндлер, реагирующий на неправильно (по формату) введенную дату или время
@router.message(or_f(StateFilter(FSMRemindersEditor.new_date),
                     StateFilter(FSMRemindersEditor.new_time)))
async def process_wrong_time_or_date(message: Message):
    # Сообщаем пользователю, что он ввел некорректные данные
    await message.answer(text=LEXICON_RU['wrong_format'],
                         reply_markup=kb_with_cancel_button())


# Хэндлер, реагирующий на кнопку ГОТОВО в режиме редактирования одного напоминания
@router.callback_query(StateFilter(FSMRemindersEditor.edit_one_reminder),
                       Text(text='complete_edit_cb'))
async def process_editing_complete(callback: CallbackQuery,
                                   state: FSMContext):
    # Сообщаем пользователю, что изменения сохранены
    await callback.message.edit_text(text=LEXICON_RU['editing_complete_msg'])
    await callback.answer()
    # Очищаем оперативную память
    await state.clear()


@router.message(StateFilter(FSMRemindersEditor.edit_one_reminder))
async def process_other_msg_in_edit_one_reminder_mod(message: Message,
                                                     state: FSMContext):
    # Получаем информацию из оперативной памяти
    reminder_info: dict[str, Any] = await state.get_data()
    reminder_text: str = reminder_info['reminder_text']
    reminder_date: date = reminder_info['reminder_date']
    reminder_time: time = reminder_info['reminder_time']

    # Показываем напоминание пользователю и просим выбрать, что он хочет изменить
    await message.answer(
        text=LEXICON_RU['not_understand'] +
             assemble_full_reminder_text(reminder_text,
                                         reminder_date,
                                         reminder_time) + LEXICON_RU['what_edit'],
        reply_markup=build_kb_to_edit_one_reminder())
