from datetime import date, time
from typing import Any

from aiogram import F, Router
from aiogram.filters import StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import DataBaseClass, TodayRemindersClass, delete_reminder
from keyboards import build_kb_to_edit_one_reminder, build_kb_with_reminder
from lexicon import LEXICON_RU
from states import FSMRemindersEditor
from utils import assemble_full_reminder_text
from utils.utils import send_not_text

router: Router = Router()


# Хэндлер, реагирующий на нажатие кнопки УДАЛИТЬ
@router.callback_query(
    StateFilter(FSMRemindersEditor.show_one_reminder),
    F.data == LEXICON_RU["delete_reminder_cb"],
)
async def process_delete_one_reminder(
    callback: CallbackQuery,
    database: DataBaseClass,
    state: FSMContext,
    today_reminders: TodayRemindersClass,
):
    # Удаляем напоминание из базы данных
    saved_info: dict[str, Any] = await state.get_data()
    await delete_reminder(database, int(saved_info["reminder_id"]))

    # Если дата заметки - сегодня:
    if saved_info["reminder_date"] == date.today():
        # Удаляем заметку из списка сегодняшних дел
        today_reminders.delete(saved_info["reminder_id"])

    # Удаляем сообщение с заметкой
    await callback.message.delete()
    # Очищаем информацию из оперативной памяти и ставим дефолтное состояние
    await state.clear()

    # Отправляем нотификацию о том, что заметка удалена
    await callback.answer(text=LEXICON_RU["reminder_was_deleted"])


# Хэндлер, реагирующий на нажатие на кнопку РЕДАКТИРОВАТЬ или на нажатие
# кнопки ОТМЕНА во время редактирования текста, даты или времени.
@router.callback_query(
    StateFilter(FSMRemindersEditor.show_one_reminder), F.data == LEXICON_RU["edit_cb"]
)
@router.callback_query(
    F.data == LEXICON_RU["cancel_cb"],
    or_f(
        StateFilter(FSMRemindersEditor.new_text),
        StateFilter(FSMRemindersEditor.new_date),
        StateFilter(FSMRemindersEditor.new_time),
    ),
)
async def process_edit_one_reminder(callback: CallbackQuery, state: FSMContext):
    # Получаем информацию из оперативной памяти
    reminder_info: dict[str, Any] = await state.get_data()
    reminder_text: str = reminder_info["reminder_text"]
    reminder_date: date = reminder_info["reminder_date"]
    reminder_time: time = reminder_info["reminder_time"]
    msg_type: str = reminder_info["msg_type"]
    user_id: int = reminder_info["user_id"]
    file_id: str = reminder_info["file_id"]

    # Показываем напоминание пользователю и просим выбрать, что он хочет изменить
    if msg_type == "text":
        await callback.message.edit_text(
            text=assemble_full_reminder_text(
                reminder_text, reminder_date, reminder_time
            )
            + LEXICON_RU["what_edit"],
            reply_markup=build_kb_to_edit_one_reminder(),
        )
    else:
        caption: str | None = await send_not_text(
            msg_type, user_id, file_id, reminder_text
        )
        await callback.message.answer(
            text=assemble_full_reminder_text(caption, reminder_date, reminder_time)
            + LEXICON_RU["what_edit"],
            reply_markup=build_kb_to_edit_one_reminder(),
        )
    await callback.answer()

    # Изменяем состояние на редактирование одной заметки
    await state.set_state(FSMRemindersEditor.edit_one_reminder)


# Хэндлер, реагирующий на кнопку НАЗАД в режиме просмотра одной заметки совмещен с\
# хендлером handlers_to_edit_list_reminders.process_exit_from_deleting_mod


# Хэндлер, реагирующий на любые другие сообщения в режиме просмотра одной заметки
@router.message(StateFilter(FSMRemindersEditor.show_one_reminder))
async def process_other_msg_in_showing_one_reminder_mod(
    message: Message, state: FSMContext
):
    # Получим необходимую информацию о заметке
    reminder_info: dict[str, Any] = await state.get_data()
    reminder_text: str = reminder_info["reminder_text"]
    reminder_date: date = reminder_info["reminder_date"]
    reminder_time: time = reminder_info["reminder_time"]

    # Говорим пользователю, что мы его не понимаем, и снова отсылаем ему напоминание
    await message.answer(
        text=LEXICON_RU["not_understand"]
        + assemble_full_reminder_text(
            reminder_text=reminder_text,
            reminder_date=reminder_date,
            reminder_time=reminder_time,
        ),
        reply_markup=build_kb_with_reminder(),
    )
