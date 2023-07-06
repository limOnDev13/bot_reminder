"""
Модуль с хэндлерами для просмотра и редактирования сохраненных заметок.
"""
from aiogram import Router, F
from aiogram.filters import Command, Text, StateFilter, or_f
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from datetime import date, timedelta, datetime, time
from asyncpg import Record
from typing import List

from keyboards import (build_kb_to_choose_date_to_show, build_kb_with_reminders,
                       build_kb_with_reminder, build_kb_to_edit_one_reminder,
                       kb_with_cancel_button)
from lexicon import LEXICON_RU
from states import FSMRemindersEditor
from database import (DataBaseClass, select_reminders, select_chosen_reminder,
                      delete_reminder, update_reminder_text, update_reminder_date,
                      update_reminder_time, show_all_reminders)
from filters import InputIsDate, ItIsInlineButtonWithReminder, InputIsTime
from utils import assemble_full_reminder_text


router: Router = Router()


PAGE_SIZE: int = 10


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
    await callback.answer()


# Обработка нажатия на клавишу Сегодня или Завтра в состоянии просмотра напоминаний
@router.message(StateFilter(FSMRemindersEditor.show_reminds),
                Text(text=[LEXICON_RU['today_bt_text'],
                           LEXICON_RU['tomorrow_bt_text']]))
async def show_today_or_tomorrow_reminders(message: Message,
                                           database: DataBaseClass,
                                           state: FSMContext):
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
                             with_time=True,
                             page_size=PAGE_SIZE
                         ))

    await state.update_data(date_of_showed_reminders=selected_date,
                            show_all_reminders=False,
                            reminders=reminders,
                            pos_first_elem=0,
                            page_size=PAGE_SIZE)


# Хэндлер для обработки правильно введенной (по формату) даты
# для просмотра списка заметок
@router.message(StateFilter(FSMRemindersEditor.show_reminds),
                InputIsDate())
async def show_reminders_on_chosen_date(message: Message,
                                        valid_date: bool | datetime,
                                        database: DataBaseClass,
                                        state: FSMContext):
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
                with_time=True,
                page_size=PAGE_SIZE
            )
        )

        await state.update_data(date_of_showed_reminders=valid_date,
                                show_all_reminders=False,
                                reminders=reminders,
                                pos_first_elem=0,
                                page_size=PAGE_SIZE)
    else:
        await message.answer(text=LEXICON_RU['past_date'])


# Хэндлер, выводящий все заметки пользователя по нажатию на кнопку Все
@router.message(Text(text=LEXICON_RU['all']),
                StateFilter(FSMRemindersEditor.show_reminds))
async def process_show_all_reminders(message: Message,
                                     state: FSMContext,
                                     database: DataBaseClass):
    reminders: List[Record] = await show_all_reminders(
        connector=database, user_id=message.from_user.id
    )
    await message.answer(text=LEXICON_RU['view_all_reminders'],
                         reply_markup=build_kb_with_reminders(
                             user_id=message.from_user.id,
                             reminders=reminders,
                             pos_first_elem=0,
                             page_size=PAGE_SIZE,
                             with_data=True
                         ))
    await state.update_data(date_of_showed_reminders=date.today(),
                            show_all_reminders=True,
                            reminders=reminders,
                            pos_first_elem=0,
                            page_size=PAGE_SIZE)
# Хэндлер на обработку остальных ответов в состоянии ввода даты
# объединен с похожим хэндлером в user_handler.py


# Хэндлер, для пагинации страниц в выведенном списке
@router.callback_query(StateFilter(FSMRemindersEditor.show_reminds),
                       Text(text=[LEXICON_RU['previous_page_cb'],
                                  LEXICON_RU['next_page_cb']]))
async def process_pagination(callback: CallbackQuery,
                             state: FSMContext):
    reminders_info = await state.get_data()
    pos_first_elem: int = reminders_info['pos_first_elem']
    page_size: int = reminders_info['page_size']
    reminders: List[Record] = reminders_info['reminders']
    all_reminders: bool = reminders_info['show_all_reminders']
    date_of_showed_reminders: date = reminders_info['date_of_showed_reminders']

    need_to_change_msg: bool

    if (callback.data == LEXICON_RU['previous_page_cb']) and \
            (pos_first_elem > 0):
        pos_first_elem -= page_size
        need_to_change_msg = True
    elif (callback.data == LEXICON_RU['next_page_cb']) and\
            (pos_first_elem + page_size < len(reminders)):
        pos_first_elem += page_size
        need_to_change_msg = True
    else:
        need_to_change_msg = False
        await callback.answer()

    if need_to_change_msg:
        msg_text: str
        with_data: bool = False
        with_time: bool = False

        if all_reminders:
            msg_text = LEXICON_RU['view_all_reminders']
            with_data = True
        elif date_of_showed_reminders == date.today():
            msg_text = LEXICON_RU['today_msg']
            with_time = True
        elif date_of_showed_reminders == date.today() + timedelta(days=1):
            msg_text = LEXICON_RU['tomorrow_msg']
            with_time = True
        else:
            msg_text = LEXICON_RU['reminders_on_chosen_date_msg'] +\
                       date_of_showed_reminders.strftime("%d.%m.%Y")
            with_time = True

        await callback.message.edit_text(text=msg_text,
                                         reply_markup=build_kb_with_reminders(
                                             user_id=callback.from_user.id,
                                             reminders=reminders,
                                             pos_first_elem=pos_first_elem,
                                             page_size=page_size,
                                             with_data=with_data,
                                             with_time=with_time
                                         ))

        await state.update_data(pos_first_elem=pos_first_elem)
        await callback.answer()



# Хэндлер, реагирующий на нажатие на заметку
@router.callback_query(ItIsInlineButtonWithReminder())
async def show_chosen_reminder(callback: CallbackQuery,
                               reminder_id: int,
                               state: FSMContext,
                               database: DataBaseClass):
    reminder: Record = await select_chosen_reminder(connector=database,
                                                    reminder_id=reminder_id)
    reminder_date: date = reminder['reminder_date']
    reminder_time: time = reminder['reminder_time']
    reminder_text: str = reminder['reminder_text']

    await state.update_data(reminder_id=reminder_id,
                            reminder_text=reminder_text,
                            reminder_date=reminder_date,
                            reminder_time=reminder_time)

    await callback.message.edit_text(
        text=assemble_full_reminder_text(reminder_text,
                                         reminder_date,
                                         reminder_time),
        reply_markup=build_kb_with_reminder()
    )

    await state.set_state(FSMRemindersEditor.show_one_reminder)
    await callback.answer()
# Хэндлер, который реагирует на обычное сообщение в состоянии просмотра
# одного напоминания уже имеется в user_handler.py


# Хэндлер, реагирующий на нажатие кнопки УДАЛИТЬ
@router.callback_query(StateFilter(FSMRemindersEditor.show_one_reminder),
                       Text(text=[LEXICON_RU['delete_reminder_cb']]))
async def process_delete_one_reminder(callback: CallbackQuery,
                                      database: DataBaseClass,
                                      state: FSMContext):
    saved_info = await state.get_data()
    await callback.answer(text=LEXICON_RU['reminder_was_deleted'])
    await delete_reminder(database, int(saved_info['reminder_id']))
    await callback.message.delete()
    await state.clear()


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
    reminder_info = await state.get_data()
    reminder_text = reminder_info['reminder_text']
    reminder_date = reminder_info['reminder_date']
    reminder_time = reminder_info['reminder_time']

    await callback.message.edit_text(
        text=assemble_full_reminder_text(reminder_text,
                                         reminder_date,
                                         reminder_time) + LEXICON_RU['what_edit'],
        reply_markup=build_kb_to_edit_one_reminder())
    await state.set_state(FSMRemindersEditor.edit_one_reminder)

    await callback.answer()


# Хэндлер, реагирующий на нажатие кнопки Текст в режиме редактирования
@router.callback_query(StateFilter(FSMRemindersEditor.edit_one_reminder),
                       Text(text=LEXICON_RU['change_text_cb']))
async def process_edit_reminder_text(callback: CallbackQuery,
                                     state: FSMContext):
    await state.set_state(FSMRemindersEditor.new_text)

    await callback.message.edit_text(text=LEXICON_RU['new_reminder_text'],
                                     reply_markup=kb_with_cancel_button())
    await callback.answer()


# Хэндлер, который сохраняет отредактированный текст в заметку
@router.message(StateFilter(FSMRemindersEditor.new_text))
async def process_enter_new_text(message: Message,
                                 state: FSMContext,
                                 database: DataBaseClass):
    reminder_info = await state.get_data()
    reminder_date = reminder_info['reminder_date']
    reminder_time = reminder_info['reminder_time']

    await update_reminder_text(database,
                               reminder_info['reminder_id'], message.text)

    await message.answer(text=assemble_full_reminder_text(message.text,
                                                          reminder_date,
                                                          reminder_time) +
                              LEXICON_RU['done'] + LEXICON_RU['what_edit'],
                         reply_markup=build_kb_to_edit_one_reminder())

    await state.update_data(reminder_text=message.text)

    await state.set_state(FSMRemindersEditor.edit_one_reminder)


# Хэндлер, реагирующий на нажатие кнопки Дату
@router.callback_query(StateFilter(FSMRemindersEditor.edit_one_reminder),
                       Text(text=LEXICON_RU['change_date_cb']))
async def process_edit_reminder_date(callback: CallbackQuery,
                                     state: FSMContext):
    await callback.message.edit_text(text=LEXICON_RU['new_reminder_date'],
                                     reply_markup=kb_with_cancel_button())

    await state.set_state(FSMRemindersEditor.new_date)

    await callback.answer()


# Обработка ввода даты в правильном формате
@router.message(StateFilter(FSMRemindersEditor.new_date), InputIsDate())
async def process_enter_new_date(message: Message,
                                 database: DataBaseClass,
                                 state: FSMContext,
                                 valid_date: bool | datetime):
    if valid_date:
        reminder_info = await state.get_data()
        reminder_text = reminder_info['reminder_text']
        reminder_time = reminder_info['reminder_time']

        await update_reminder_date(database,
                                   reminder_info['reminder_id'],
                                   valid_date.date())

        await message.answer(text=assemble_full_reminder_text(reminder_text,
                                                              valid_date.date(),
                                                              reminder_time) +
                                  LEXICON_RU['done'] + LEXICON_RU['what_edit'],
                             reply_markup=build_kb_to_edit_one_reminder())

        await state.update_data(reminder_date=valid_date.date())
        await state.set_state(FSMRemindersEditor.edit_one_reminder)

    else:
        await message.answer(text=LEXICON_RU['past_date'],
                             reply_markup=kb_with_cancel_button())


# Хэндлер, реагирующий на нажатие кнопки Время
@router.callback_query(StateFilter(FSMRemindersEditor.edit_one_reminder),
                       Text(text=LEXICON_RU['change_time_cb']))
async def process_edit_reminder_time(callback: CallbackQuery,
                                     state: FSMContext):
    await callback.message.edit_text(text=LEXICON_RU['new_reminder_time'],
                                     reply_markup=kb_with_cancel_button())

    await state.set_state(FSMRemindersEditor.new_time)

    await callback.answer()


# Хэндлер, реагирующий на правильно (по формату) введенное время
@router.message(StateFilter(FSMRemindersEditor.new_date), InputIsTime())
async def process_enter_new_date(message: Message,
                                 database: DataBaseClass,
                                 state: FSMContext,
                                 selected_more_current: bool,
                                 valid_time: datetime):
    reminder_info = await state.get_data()
    reminder_text: str = reminder_info['reminder_text']
    reminder_date: date = reminder_info['reminder_date']

    if (reminder_date == date.today()) and selected_more_current:
        await update_reminder_time(database,
                                   reminder_info['reminder_id'],
                                   valid_time.time())

        await message.answer(text=assemble_full_reminder_text(reminder_text,
                                                              reminder_date,
                                                              valid_time.time()) +
                                  LEXICON_RU['done'] + LEXICON_RU['what_edit'],
                             reply_markup=build_kb_to_edit_one_reminder())

        await state.update_data(reminder_time=valid_time.time())
        await state.set_state(FSMRemindersEditor.edit_one_reminder)
    else:
        await message.answer(text=LEXICON_RU['past_time'],
                             reply_markup=kb_with_cancel_button())


@router.message(or_f(StateFilter(FSMRemindersEditor.new_date),
                     StateFilter(FSMRemindersEditor.new_time)))
async def process_wrong_time_or_date(message: Message):
    await message.answer(text=LEXICON_RU['wrong_format'],
                         reply_markup=kb_with_cancel_button())


@router.callback_query(StateFilter(FSMRemindersEditor.edit_one_reminder),
                       Text(text='complete_edit_cb'))
async def process_editing_complete(callback: CallbackQuery,
                                   state: FSMContext):
    await callback.message.edit_text(text=LEXICON_RU['editing_complete_msg'])
    await state.clear()

