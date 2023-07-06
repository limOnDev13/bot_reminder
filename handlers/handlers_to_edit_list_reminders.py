from aiogram import Router
from aiogram.filters import Text, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import date, timedelta
from asyncpg import Record
from typing import List, Any

from keyboards import (build_kb_to_edit_list_reminders, build_kb_with_reminders)
from lexicon import LEXICON_RU
from states import FSMRemindersEditor
from database import (DataBaseClass, delete_reminder)
from filters import (ItIsReminderForDeleting)


router: Router = Router()


# Хэндлер, реагирующий на нажатие на кнопку в режиме редактирования списка напоминаний
@router.callback_query(StateFilter(FSMRemindersEditor.edit_reminds),
                       ItIsReminderForDeleting())
async def process_delete_reminder_from_list(callback: CallbackQuery,
                                            state: FSMContext,
                                            database: DataBaseClass,
                                            reminder_id: int):
    # Удаляем из бд
    await delete_reminder(connector=database, reminder_id=reminder_id)

    # Удаляем из оперативной памяти
    reminders_info: dict[str, Any] = await state.get_data()
    reminders: List[Record] = reminders_info['reminders']

    for index in range(len(reminders)):
        if reminders[index]['reminder_id'] == reminder_id:
            reminders.pop(index)
            break

    # Отправляем аллерт о том, что заметка удалена
    await callback.answer(text=LEXICON_RU['reminder_was_deleted'],
                          show_alert=True)

    # Отправляем сообщение с отредактированным списком заметок пользователю
    pos_first_elem: int = reminders_info['pos_first_elem']
    page_size: int = reminders_info['page_size']
    view_all_reminders: bool = reminders_info['show_all_reminders']

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


# Хэндлер, обрабатывающий нажатие на кнопку ОТМЕНА в режиме удаления заметок
# из списка и нажатие на кнопку НАЗАД в режиме просмотра одной заметки
@router.callback_query(StateFilter(FSMRemindersEditor.edit_reminds),
                       Text(text=LEXICON_RU['cancel_cb']))
@router.callback_query(StateFilter(FSMRemindersEditor.show_one_reminder),
                       Text(text=LEXICON_RU['back_to_reminders_menu_cb']))
async def process_exit_from_deleting_mod(callback: CallbackQuery,
                                         state: FSMContext):
    # Меняем состояние на просмотр списка заметок
    await state.set_state(FSMRemindersEditor.show_reminds)

    # Меняем сообщение на просмотр списка заметок с соответствующей клавиатурой
    reminders_info: dict[str, Any] = await state.get_data()
    reminders: List[Record] = reminders_info['reminders']
    pos_first_elem: int = reminders_info['pos_first_elem']
    page_size: int = reminders_info['page_size']
    view_all_reminders: bool = reminders_info['show_all_reminders']
    date_of_showed_reminders: date = reminders_info['date_of_showed_reminders']

    with_date: bool = False
    with_time: bool = False
    text_msg: str

    if view_all_reminders:
        with_date = True
        text_msg = LEXICON_RU['view_all_reminders']
    else:
        with_time = True
        text_msg = LEXICON_RU['reminders_on_chosen_date_msg'] + \
                   date_of_showed_reminders.strftime("%d.%m.%Y")

    await callback.message.edit_text(
        text=text_msg,
        reply_markup=build_kb_with_reminders(
            user_id=callback.from_user.id,
            reminders=reminders,
            pos_first_elem=pos_first_elem,
            page_size=page_size,
            with_data=with_date,
            with_time=with_time
        )
    )


# Хэндлер, отвечающий за пагинацию в режиме редактирования списка заметок
@router.callback_query(StateFilter(FSMRemindersEditor.edit_reminds),
                       Text(text=[LEXICON_RU['previous_page_cb'],
                                  LEXICON_RU['next_page_cb']]))
async def process_pagination_in_del_list(callback: CallbackQuery,
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
                                         reply_markup=build_kb_to_edit_list_reminders(
                                             user_id=callback.from_user.id,
                                             reminders=reminders,
                                             pos_first_elem=pos_first_elem,
                                             page_size=page_size,
                                             with_date=with_data,
                                             with_time=with_time
                                         ))
        await callback.answer()

        # Обновим информацию в оперативной памяти
        await state.update_data(pos_first_elem=pos_first_elem)


# Хэндлер, реагирующий на все остальные сообщение в режиме редактирования
# списка заметок
@router.message(StateFilter(FSMRemindersEditor.edit_reminds))
async def other_message_in_editing_list_mod(message: Message,
                                            state: FSMContext):
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
                         reply_markup=build_kb_to_edit_list_reminders(
                             user_id=message.from_user.id,
                             reminders=reminders,
                             pos_first_elem=pos_first_elem,
                             page_size=page_size,
                             with_date=with_date,
                             with_time=with_time
                         ))
