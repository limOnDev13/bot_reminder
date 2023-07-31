"""
Модуль с хэндлерами для просмотра и редактирования сохраненных заметок.
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
                       build_kb_with_reminder, build_kb_to_edit_list_reminders)
from lexicon import LEXICON_RU
from states import FSMRemindersEditor
from database import (DataBaseClass, select_reminders, select_chosen_reminder,
                      show_all_reminders)
from filters import (InputIsDate, ItIsInlineButtonWithReminder, ItIsPageNumber)
from utils import assemble_full_reminder_text
from utils.utils import send_not_text


router: Router = Router()


PAGE_SIZE: int = 10


# Обработка команды /reminders
@router.message(Command(commands=['reminders']), StateFilter(default_state))
async def process_reminders_command(message: Message, state: FSMContext):
    # Просим пользователя выбрать день на который показать заметки
    # (или показать сразу все заметки)
    await message.answer(text=LEXICON_RU['reminders'],
                         reply_markup=build_kb_to_choose_date_to_show())
    # Изменяем состояние на ввод даты для просмотра списка
    await state.set_state(FSMRemindersEditor.fill_date_to_show_reminders)


# Обработка нажатия на кнопку ОТМЕНА в состоянии ввода даты для просмотра
# списка заметок
@router.message(StateFilter(FSMRemindersEditor.fill_date_to_show_reminders),
                Text(text=LEXICON_RU['cancel_bt_text']))
async def process_cancel_enter_date_to_view_reminders(message: Message,
                                                      state: FSMContext):
    # Удаляем клавиатуру и пишем, что пользователь может сохранить заметку
    await message.answer(
        text=LEXICON_RU['cancel_view_msg'],
        reply_markup=ReplyKeyboardRemove()
    )
    await state.clear()


# Обработка нажатия на кнопку НОВАЯ ЗАМЕТКА в состоянии просмотра одной заметки,
# или на кнопку НАЗАД в состоянии просмотра списка заметок
@router.callback_query(StateFilter(FSMRemindersEditor.show_reminds),
                       Text(text=LEXICON_RU['back_cb']))
@router.callback_query(StateFilter(FSMRemindersEditor.show_one_reminder),
                       Text(text=LEXICON_RU['enter_new_reminder_cb']))
async def process_cancel_view_reminders(callback: CallbackQuery,
                                        state: FSMContext):
    # Удаляем информацию из оперативной памяти
    await state.clear()
    # Сообщаем пользователю, что он может сохранить новые заметки
    await callback.message.edit_text(text=LEXICON_RU['cancel_view_msg'])
    await callback.answer()


# Обработка нажатия на клавишу Сегодня или Завтра в состоянии ввода даты для
# просмотра напоминаний, или команды /today и /tomorrow в дефолтном состоянии
@router.message(StateFilter(FSMRemindersEditor.fill_date_to_show_reminders),
                Text(text=[LEXICON_RU['today_bt_text'],
                           LEXICON_RU['tomorrow_bt_text']]))
@router.message(StateFilter(default_state),
                Command(commands=['today', 'tomorrow']))
async def show_today_or_tomorrow_reminders(message: Message,
                                           database: DataBaseClass,
                                           state: FSMContext):
    # Удаляем сообщение предыдущее сообщение, чтобы старая клавиатура не мешалась
    await message.answer(text=LEXICON_RU['sec_please'],
                         reply_markup=ReplyKeyboardRemove())

    # В зависимости от выбранного дня будут разные даты и тексты сообщений
    reminders: List[Record]
    msg_text: str
    selected_date: date

    # Если выбран сегодняшний день
    if (message.text == LEXICON_RU['today_bt_text']) or\
            (message.text == '/today'):
        # Укажем сегодняшний день и соответсвующее сообщение пользователю
        selected_date = date.today()
        msg_text = LEXICON_RU['today_msg']
    # Если выбран завтрашний день
    else:
        # Укажем завтрашний день и соответсвующее сообщение пользователю
        selected_date = date.today() + timedelta(days=1)
        msg_text = LEXICON_RU['tomorrow_msg']

    # Достанем необходимую информацию из базы данных
    reminders = await select_reminders(
        connector=database,
        user_id=message.from_user.id,
        reminder_date=selected_date
    )

    # Сохраним данные в оперативной памяти
    await state.update_data(date_of_showed_reminders=selected_date,
                            show_all_reminders=False,
                            reminders=reminders,
                            pos_first_elem=0,
                            page_size=PAGE_SIZE)

    # Изменим состояние на просмотр списка заметок
    await state.set_state(FSMRemindersEditor.show_reminds)

    # Отправим пользователю клавиатуру с заметками
    await message.answer(text=msg_text,
                         reply_markup=build_kb_with_reminders(
                             user_id=message.from_user.id,
                             reminders=reminders,
                             pos_first_elem=0,
                             with_time=True,
                             page_size=PAGE_SIZE
                         ))


# Хэндлер для обработки правильно введенной (по формату) даты
# для просмотра списка заметок
@router.message(StateFilter(FSMRemindersEditor.fill_date_to_show_reminders),
                InputIsDate())
async def show_reminders_on_chosen_date(message: Message,
                                        valid_date: bool | datetime,
                                        database: DataBaseClass,
                                        state: FSMContext):
    # Если пришла корректная дата, которая ЕЩЕ НЕ прошла
    if valid_date:
        # Удаляем сообщение предыдущее сообщение, чтобы старая клавиатура не мешалась
        await message.answer(text=LEXICON_RU['sec_please'],
                             reply_markup=ReplyKeyboardRemove())

        # Достанем необходимую информацию из базы данных
        reminders: List[Record] = await select_reminders(
            connector=database,
            user_id=message.from_user.id,
            reminder_date=valid_date.date()
        )

        # Сохраним данные в оперативной памяти
        await state.update_data(date_of_showed_reminders=valid_date,
                                show_all_reminders=False,
                                reminders=reminders,
                                pos_first_elem=0,
                                page_size=PAGE_SIZE)

        # Изменим состояние на просмотр списка заметок
        await state.set_state(FSMRemindersEditor.show_reminds)

        # Пришлем пользователю клавиатуру с заметками на выбранную дату
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
    # Если пришла корректная дата, которая УЖЕ прошла
    else:
        await message.answer(text=LEXICON_RU['past_date'])


# Хэндлер, выводящий все заметки пользователя по нажатию на кнопку Все
@router.message(Text(text=LEXICON_RU['all']),
                StateFilter(FSMRemindersEditor.fill_date_to_show_reminders))
async def process_show_all_reminders(message: Message,
                                     state: FSMContext,
                                     database: DataBaseClass):
    # Удаляем сообщение предыдущее сообщение, чтобы старая клавиатура не мешалась
    await message.answer(text=LEXICON_RU['sec_please'],
                         reply_markup=ReplyKeyboardRemove())

    # Достанем все напоминания из базы данных
    reminders: List[Record] = await show_all_reminders(
        connector=database, user_id=message.from_user.id
    )

    # Сохраним данные в оперативной памяти
    await state.update_data(date_of_showed_reminders=date.today(),
                            show_all_reminders=True,
                            reminders=reminders,
                            pos_first_elem=0,
                            page_size=PAGE_SIZE)

    # Изменим состояние на просмотр списка заметок
    await state.set_state(FSMRemindersEditor.show_reminds)

    # Отправим пользователю клавиатуру со всеми заметками
    await message.answer(text=LEXICON_RU['view_all_reminders'],
                         reply_markup=build_kb_with_reminders(
                             user_id=message.from_user.id,
                             reminders=reminders,
                             pos_first_elem=0,
                             page_size=PAGE_SIZE,
                             with_data=True
                         ))


# Хэндлер, реагирующий на все остальные сообщения в состоянии ввода даты для
# просмотра списка заметок
@router.message(StateFilter(FSMRemindersEditor.fill_date_to_show_reminders))
async def process_enter_not_date(message: Message):
    # Сообщаем пользователю, что мы его не понимаем, и просим ввести дату
    await message.answer(text=LEXICON_RU['not_understand'] +
                              LEXICON_RU['reminders'],
                         reply_markup=build_kb_to_choose_date_to_show())


# Хэндлер для пагинации страниц в просматриваемом списке
@router.callback_query(StateFilter(FSMRemindersEditor.show_reminds),
                       Text(text=[LEXICON_RU['previous_page_cb'],
                                  LEXICON_RU['next_page_cb']]))
async def process_pagination(callback: CallbackQuery,
                             state: FSMContext):
    # Достанем необходимую информацию из оперативной памяти
    reminders_info = await state.get_data()
    pos_first_elem: int = reminders_info['pos_first_elem']
    page_size: int = reminders_info['page_size']
    reminders: List[Record] = reminders_info['reminders']

    need_to_change_msg: bool
    # Если пользователь находится не в самом начале, и он нажал на кнопку <<
    if (callback.data == LEXICON_RU['previous_page_cb']) and \
            (pos_first_elem > 0):
        # Уменьшим позицию первой отображаемой заметки на длину отображаемого списка
        pos_first_elem -= page_size
        need_to_change_msg = True
    # Если пользователь находится не в самом конце, и он нажал на кнопку >>
    elif (callback.data == LEXICON_RU['next_page_cb']) and\
            (pos_first_elem + page_size < len(reminders)):
        # Увеличим позицию первой отображаемой заметки на длину отображаемого списка
        pos_first_elem += page_size
        need_to_change_msg = True
    # Если пользователь нажимает << в самом начале или >> в самом конце
    else:
        # Нам не нужно ничего менять
        need_to_change_msg = False
        await callback.answer()

    # Если мы меняли отображаемый список (листали его)
    if need_to_change_msg:
        all_reminders: bool = reminders_info['show_all_reminders']
        date_of_showed_reminders: date = reminders_info['date_of_showed_reminders']

        msg_text: str
        with_data: bool = False
        with_time: bool = False

        # В зависимости от того, что мы выводили ранее (все заметки,
        # заметки на сегодня и пр.) будут разниться текст сообщения и формат
        # выводимых заметок (с датой или временем)
        # Если до этого выводили все заметки
        if all_reminders:
            msg_text = LEXICON_RU['view_all_reminders']
            with_data = True
        # Если до этого выводили заметки на сегодня
        elif date_of_showed_reminders == date.today():
            msg_text = LEXICON_RU['today_msg']
            with_time = True
        # Если до этого выводили заметки на сегодня
        elif date_of_showed_reminders == date.today() + timedelta(days=1):
            msg_text = LEXICON_RU['tomorrow_msg']
            with_time = True
        # Если до этого выводили заметки на определенную дату
        else:
            msg_text = LEXICON_RU['reminders_on_chosen_date_msg'] +\
                       date_of_showed_reminders.strftime("%d.%m.%Y")
            with_time = True

        # Отправим пользователю список заметок
        await callback.message.edit_text(text=msg_text,
                                         reply_markup=build_kb_with_reminders(
                                             user_id=callback.from_user.id,
                                             reminders=reminders,
                                             pos_first_elem=pos_first_elem,
                                             page_size=page_size,
                                             with_data=with_data,
                                             with_time=with_time
                                         ))
        await callback.answer()

        # Обновим информацию в оперативной памяти
        await state.update_data(pos_first_elem=pos_first_elem)


# Хэндлер, который реагирует на нажатие кнопки с количеством напоминаний
# в состояниях просмотра и редактирования списка заметок
@router.callback_query(or_f(StateFilter(FSMRemindersEditor.show_reminds),
                            StateFilter(FSMRemindersEditor.edit_reminds)),
                       ItIsPageNumber())
async def process_view_number_reminders(callback: CallbackQuery,
                                        state: FSMContext):
    # Получим список всех запрошенных заметок и узнаем его длину
    reminder_info = await state.get_data()
    reminders: List[Record] = reminder_info['reminders']
    number_reminders: int = len(reminders)

    # Отправим пользователю нотификацию с указанием общего количества
    # запрошенных заметок
    await callback.answer(text=LEXICON_RU['number_showed_reminders'] +
                               str(number_reminders))


# Хэндлер, реагирующий на нажатие на заметку
@router.callback_query(ItIsInlineButtonWithReminder())
async def show_chosen_reminder(callback: CallbackQuery,
                               reminder_id: int,
                               state: FSMContext,
                               database: DataBaseClass):
    # Получим информацию о выбранной заметке из базы данных
    reminder: Record = await select_chosen_reminder(connector=database,
                                                    reminder_id=reminder_id)
    reminder_date: date = reminder['reminder_date']
    reminder_time: time = reminder['reminder_time']
    reminder_text: str = reminder['reminder_text']
    msg_type: str = reminder['msg_type']
    user_id: int = reminder['user_id']
    file_id: str = reminder['file_id']

    # Сохраним необходимую информацию в оперативной памяти
    await state.update_data(reminder_id=reminder_id,
                            reminder_text=reminder_text,
                            reminder_date=reminder_date,
                            reminder_time=reminder_time,
                            msg_type=msg_type,
                            user_id=user_id,
                            file_id=file_id)

    # Изменим состояние на просмотр одной заметки
    await state.set_state(FSMRemindersEditor.show_one_reminder)

    await callback.message.delete()

    if msg_type == 'text':
        # Отправим выбранную заметку пользователю
        await callback.message.answer(
            text=assemble_full_reminder_text(reminder_text,
                                             reminder_date,
                                             reminder_time),
            reply_markup=build_kb_with_reminder()
        )
    else:
        caption: str | None = await send_not_text(msg_type=msg_type, user_id=user_id,
                                                  file_id=file_id, reminder_text=reminder_text)

        await callback.message.answer(text=assemble_full_reminder_text(reminder_text=caption,
                                                                       reminder_date=reminder_date,
                                                                       reminder_time=reminder_time),
                                      reply_markup=build_kb_with_reminder())

    await callback.answer()


# Хэндлер, реагирующий на кнопку РЕДАКТИРОВАТЬ в списке заметок
@router.callback_query(StateFilter(FSMRemindersEditor.show_reminds),
                       Text(text=LEXICON_RU['edit_cb']))
async def process_edit_list_reminders(callback: CallbackQuery,
                                      state: FSMContext):
    reminders_info = await state.get_data()
    reminders: List[Record] = reminders_info['reminders']
    pos_first_elem: int = reminders_info['pos_first_elem']
    view_all_reminders: bool = reminders_info['show_all_reminders']
    page_size: int = reminders_info['page_size']

    with_date: bool = False
    with_time: bool = False

    if view_all_reminders:
        with_date = True
    else:
        with_time = True

    await callback.message.edit_text(
        text=LEXICON_RU['what_reminders_delete'],
        reply_markup=build_kb_to_edit_list_reminders(
            user_id=callback.from_user.id,
            reminders=reminders,
            pos_first_elem=pos_first_elem,
            page_size=page_size,
            with_date=with_date,
            with_time=with_time
        )
    )

    await state.set_state(FSMRemindersEditor.edit_reminds)
    await callback.answer()


# Хэндлер, который реагирует на обычное сообщение в состоянии просмотра
# списка заметок
@router.message(StateFilter(FSMRemindersEditor.show_reminds))
async def process_other_message_in_reminders(message: Message, state: FSMContext):
    # Получим все необходимые данные из оперативной памяти
    reminders_info: dict[str, Any] = await state.get_data()
    reminders: List[Record] = reminders_info['reminders']
    pos_first_elem: int = reminders_info['pos_first_elem']
    page_size: int = reminders_info['page_size']
    view_all_reminders: bool = reminders_info['show_all_reminders']

    with_date: bool = False
    with_time: bool = False

    if view_all_reminders:
        with_date = True
    else:
        with_time = True

    # Изменим текст сообщения и скажем, что не понимаем пользователя
    await message.answer(text=LEXICON_RU['not_understand'],
                         reply_markup=build_kb_with_reminders(
                             user_id=message.from_user.id,
                             reminders=reminders,
                             pos_first_elem=pos_first_elem,
                             page_size=page_size,
                             with_data=with_date,
                             with_time=with_time
                         ))
