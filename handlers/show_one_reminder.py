from aiogram import Router
from aiogram.filters import Text, StateFilter, or_f
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import date, time
from typing import Any

from keyboards import (build_kb_with_reminder, build_kb_to_edit_one_reminder)
from lexicon import LEXICON_RU
from states import FSMRemindersEditor
from database import (DataBaseClass, delete_reminder, TodayRemindersClass)
from utils import assemble_full_reminder_text


router: Router = Router()


# Хэндлер, реагирующий на нажатие кнопки УДАЛИТЬ
@router.callback_query(StateFilter(FSMRemindersEditor.show_one_reminder),
                       Text(text=[LEXICON_RU['delete_reminder_cb']]))
async def process_delete_one_reminder(callback: CallbackQuery,
                                      database: DataBaseClass,
                                      state: FSMContext,
                                      today_reminders: TodayRemindersClass):
    # Удаляем напоминание из базы данных
    saved_info: dict[str, Any] = await state.get_data()
    await delete_reminder(database, int(saved_info['reminder_id']))

    # Если дата заметки - сегодня:
    if saved_info['reminder_date'] == date.today():
        # Удаляем заметку из списка сегодняшних дел
        today_reminders.delete(saved_info['reminder_id'])

    # Удаляем сообщение с заметкой
    await callback.message.delete()
    # Очищаем информацию из оперативной памяти и ставим дефолтное состояние
    await state.clear()

    # Отправляем нотификацию о том, что заметка удалена
    await callback.answer(text=LEXICON_RU['reminder_was_deleted'])


# Хэндлер, реагирующий на нажатие на кнопку РЕДАКТИРОВАТЬ или на нажатие
# кнопки ОТМЕНА во время редактирования текста, даты или времени.
@router.callback_query(StateFilter(FSMRemindersEditor.show_one_reminder),
                       Text(text=[LEXICON_RU['edit_cb']]))
@router.callback_query(Text(text=[LEXICON_RU['cancel_cb']]),
                       or_f(StateFilter(FSMRemindersEditor.new_text),
                            StateFilter(FSMRemindersEditor.new_date),
                            StateFilter(FSMRemindersEditor.new_time)))
async def process_edit_one_reminder(callback: CallbackQuery,
                                    state: FSMContext):
    # Получаем информацию из оперативной памяти
    reminder_info: dict[str, Any] = await state.get_data()
    reminder_text: str = reminder_info['reminder_text']
    reminder_date: date = reminder_info['reminder_date']
    reminder_time: time = reminder_info['reminder_time']

    # Показываем напоминание пользователю и просим выбрать, что он хочет изменить
    await callback.message.edit_text(
        text=assemble_full_reminder_text(reminder_text,
                                         reminder_date,
                                         reminder_time) + LEXICON_RU['what_edit'],
        reply_markup=build_kb_to_edit_one_reminder())
    await callback.answer()

    # Изменяем состояние на редактирование одной заметки
    await state.set_state(FSMRemindersEditor.edit_one_reminder)


# Хэндлер, реагирующий на кнопку НАЗАД в режиме просмотра одной заметки совмещен с\
# хендлером handlers_to_edit_list_reminders.process_exit_from_deleting_mod


# Хэндлер, реагирующий на любые другие сообщения в режиме просмотра одной заметки
@router.message(StateFilter(FSMRemindersEditor.show_one_reminder))
async def process_other_msg_in_showing_one_reminder_mod(message: Message,
                                                        state: FSMContext):
    # Получим необходимую информацию о заметке
    reminder_info: dict[str, Any] = await state.get_data()
    reminder_text: str = reminder_info['reminder_text']
    reminder_date: date = reminder_info['reminder_date']
    reminder_time: time = reminder_info['reminder_time']

    # Говорим пользователю, что мы его не понимаем, и снова отсылаем ему напоминание
    await message.answer(text=LEXICON_RU['not_understand'] +
                              assemble_full_reminder_text(reminder_text=reminder_text,
                                                          reminder_date=reminder_date,
                                                          reminder_time=reminder_time
                                                          ),
                         reply_markup=build_kb_with_reminder())
