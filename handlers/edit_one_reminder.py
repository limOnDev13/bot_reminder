"""
Модуль с хэндлерами, которые отвечают за работу бота при редактировании
 одного напоминания
"""

from datetime import date, datetime, time
from typing import Any

from aiogram import F, Router
from aiogram.filters import StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from asyncpg import Record

from database import (
    DataBaseClass,
    TodayRemindersClass,
    select_chosen_reminder,
    update_reminder_date,
    update_reminder_text,
    update_reminder_time,
)
from filters import CorrectDateToModifyReminder, InputIsTime
from keyboards import build_kb_to_edit_one_reminder, kb_with_cancel_button
from lexicon import LEXICON_RU
from states import FSMRemindersEditor
from utils import assemble_full_reminder_text
from utils.utils import send_not_text

router: Router = Router()


async def _send_modified_reminder(message: Message, state: FSMContext):
    reminder_info: dict[str, Any] = await state.get_data()
    msg_type: str = reminder_info["msg_type"]
    reminder_text: str = reminder_info["reminder_text"]
    reminder_date: date = reminder_info["reminder_date"]
    reminder_time: time = reminder_info["reminder_time"]

    if msg_type == "text":
        await message.answer(
            text=assemble_full_reminder_text(
                reminder_text, reminder_date, reminder_time
            )
            + LEXICON_RU["done"]
            + LEXICON_RU["what_edit"],
            reply_markup=build_kb_to_edit_one_reminder(),
        )
    else:
        user_id: int = reminder_info["user_id"]
        file_id: str = reminder_info["file_id"]

        caption: str | None = await send_not_text(
            msg_type=msg_type,
            user_id=user_id,
            file_id=file_id,
            reminder_text=reminder_text,
        )
        await message.answer(
            text=assemble_full_reminder_text(caption, reminder_date, reminder_time)
            + LEXICON_RU["done"]
            + LEXICON_RU["what_edit"],
            reply_markup=build_kb_to_edit_one_reminder(),
        )


# Хэндлер, реагирующий на нажатие кнопки Текст в режиме редактирования
@router.callback_query(
    StateFilter(FSMRemindersEditor.edit_one_reminder),
    F.data == LEXICON_RU["change_text_cb"],
)
async def process_edit_reminder_text(callback: CallbackQuery, state: FSMContext):
    # Проверим тип сообщения
    saved_info: dict[str, Any] = await state.get_data()
    msg_type: str = saved_info["msg_type"]

    if msg_type in {"video_note", "voice"}:
        await callback.answer(text=LEXICON_RU["can_not_change_text"], show_alert=True)
    else:
        # Установим состояние ввода нового текста
        await state.set_state(FSMRemindersEditor.new_text)
        # Отправим пользователю просьбу ввести новый текст заметки
        await callback.message.edit_text(
            text=LEXICON_RU["new_reminder_text"], reply_markup=kb_with_cancel_button()
        )
        await callback.answer()


# Хэндлер, который сохраняет отредактированный текст в заметку
@router.message(StateFilter(FSMRemindersEditor.new_text))
async def process_enter_new_text(
    message: Message,
    state: FSMContext,
    database: DataBaseClass,
    today_reminders: TodayRemindersClass,
):
    # Обновим базу данных
    reminder_info = await state.get_data()

    await update_reminder_text(database, reminder_info["reminder_id"], message.text)

    # Обновим информацию в оперативной памяти
    await state.update_data(reminder_text=message.text)

    # Если дата заметки - сегодня
    if reminder_info["reminder_date"] == date.today():
        # Изменим соответствующую заметку в списке сегодняшних заметок
        new_reminder: Record = await select_chosen_reminder(
            connector=database, reminder_id=reminder_info["reminder_id"]
        )
        today_reminders.delete(new_reminder)
        today_reminders.push([new_reminder])

    # Покажем обновленную заметку и спросим что еще нужно изменить
    await _send_modified_reminder(message, state)

    # Перейдем обратно в режим редактирования одной заметки
    await state.set_state(FSMRemindersEditor.edit_one_reminder)


# Хэндлер, реагирующий на нажатие кнопки Дату
@router.callback_query(
    StateFilter(FSMRemindersEditor.edit_one_reminder),
    F.data == LEXICON_RU["change_date_cb"],
)
async def process_edit_reminder_date(callback: CallbackQuery, state: FSMContext):
    # Изменим состояние на ввод новой даты
    await state.set_state(FSMRemindersEditor.new_date)

    # Попросим ввести валидную дату
    await callback.message.edit_text(
        text=LEXICON_RU["new_reminder_date"], reply_markup=kb_with_cancel_button()
    )
    await callback.answer()


# Обработка ввода даты в правильном формате
@router.message(StateFilter(FSMRemindersEditor.new_date), CorrectDateToModifyReminder())
async def process_enter_new_date(
    message: Message,
    database: DataBaseClass,
    state: FSMContext,
    valid_date: bool | datetime,
    today_reminders: TodayRemindersClass,
):
    # Если пользователь прислал валидную дату, которая ЕЩЕ НЕ прошла
    if valid_date:
        # Обновим информацию в базе данных
        reminder_info = await state.get_data()
        await update_reminder_date(
            database, reminder_info["reminder_id"], valid_date.date()
        )

        # Обновим информацию в оперативной памяти
        await state.update_data(reminder_date=valid_date.date())

        # Получим измененную заметку
        new_reminder = await select_chosen_reminder(
            connector=database, reminder_id=reminder_info["reminder_id"]
        )
        # Если выбранная дата - сегодня
        if valid_date == date.today():
            # Добавим ее в список сегодняшних заметок
            today_reminders.push([new_reminder])
        # Если выбранная дата - НЕ сегодня
        else:
            # Удалим ее из списка сегодняшних заметок (если она там есть)
            today_reminders.delete(reminder=new_reminder)

        # Отправим пользователю обновленную заметку и спросим, что еще нужно изменить
        await _send_modified_reminder(message, state)

        # Изменим состояние на редактирование одной заметки
        await state.set_state(FSMRemindersEditor.edit_one_reminder)
    # Если пользователь прислал валидную дату, которая УЖЕ прошла
    else:
        # Сообщаем пользователю, что дата уже прошла и нужно ввести корректную дату
        await message.answer(
            text=LEXICON_RU["past_date"], reply_markup=kb_with_cancel_button()
        )


# Хэндлер, реагирующий на нажатие кнопки Время
@router.callback_query(
    StateFilter(FSMRemindersEditor.edit_one_reminder),
    F.data == LEXICON_RU["change_time_cb"],
)
async def process_edit_reminder_time(callback: CallbackQuery, state: FSMContext):
    # Меняем состояние на ввод нового времени
    await state.set_state(FSMRemindersEditor.new_time)

    # Просим пользователя ввести новое время
    await callback.message.edit_text(
        text=LEXICON_RU["new_reminder_time"], reply_markup=kb_with_cancel_button()
    )
    await callback.answer()


# Хэндлер, реагирующий на правильно (по формату) введенное время
@router.message(StateFilter(FSMRemindersEditor.new_time), InputIsTime())
async def process_enter_correct_date(
    message: Message,
    database: DataBaseClass,
    state: FSMContext,
    selected_more_current: bool,
    valid_time: datetime,
    today_reminders: TodayRemindersClass,
):
    # Получим информацию о заметке из оперативной памяти
    reminder_info = await state.get_data()
    reminder_date: date = reminder_info["reminder_date"]

    # Если пользователь выбрал сегодняшний день и ввел время, которое больше чем
    # текущее (сегодня еще не прошло), или любой другой день
    if ((reminder_date == date.today()) and selected_more_current) or (
        reminder_date > date.today()
    ):
        # Обновим информацию в базе данных
        await update_reminder_time(
            database, reminder_info["reminder_id"], valid_time.time()
        )

        # Обновим информацию в оперативной памяти
        await state.update_data(reminder_time=valid_time.time())

        # Если дата заметки - сегодня
        if reminder_info["reminder_date"] == date.today():
            # Изменим соответствующую заметку в списке сегодняшних заметок
            new_reminder: Record = await select_chosen_reminder(
                connector=database, reminder_id=reminder_info["reminder_id"]
            )
            print(new_reminder["reminder_id"])
            today_reminders.delete(new_reminder)
            today_reminders.push([new_reminder])

        # Покажем пользователю обновленную заметку и спросим, что еще нужно изменить
        await _send_modified_reminder(message, state)

        # Изменим состояние на редактирование одной заметки
        await state.set_state(FSMRemindersEditor.edit_one_reminder)
    # Если пользователь выбрал сегодняшнюю дату и время, которое прошло
    else:
        # Сообщаем пользователю, что он выбрал время, которое сегодня уже прошло,
        # и просим ввести корректное время
        await message.answer(
            text=LEXICON_RU["past_time"], reply_markup=kb_with_cancel_button()
        )


# Хэндлер, реагирующий на неправильно (по формату) введенную дату или время
@router.message(
    or_f(
        StateFilter(FSMRemindersEditor.new_date),
        StateFilter(FSMRemindersEditor.new_time),
    )
)
async def process_wrong_time_or_date(message: Message):
    # Сообщаем пользователю, что он ввел некорректные данные
    await message.answer(
        text=LEXICON_RU["wrong_format"], reply_markup=kb_with_cancel_button()
    )


# Хэндлер, реагирующий на кнопку ГОТОВО в режиме редактирования одного напоминания
@router.callback_query(
    StateFilter(FSMRemindersEditor.edit_one_reminder), F.data == "complete_edit_cb"
)
async def process_editing_complete(callback: CallbackQuery, state: FSMContext):
    # Сообщаем пользователю, что изменения сохранены
    await callback.message.edit_text(text=LEXICON_RU["editing_complete_msg"])
    await callback.answer()
    # Очищаем оперативную память
    await state.clear()


# Хэндлер, реагирующий на ввод остальных сообщений в режиме редактирования одной заметки
@router.message(StateFilter(FSMRemindersEditor.edit_one_reminder))
async def process_other_msg_in_edit_one_reminder_mod(
    message: Message, state: FSMContext
):
    # Получаем информацию из оперативной памяти
    reminder_info: dict[str, Any] = await state.get_data()
    reminder_text: str = reminder_info["reminder_text"]
    reminder_date: date = reminder_info["reminder_date"]
    reminder_time: time = reminder_info["reminder_time"]

    # Показываем напоминание пользователю и просим выбрать, что он хочет изменить
    await message.answer(
        text=LEXICON_RU["not_understand"]
        + assemble_full_reminder_text(reminder_text, reminder_date, reminder_time)
        + LEXICON_RU["what_edit"],
        reply_markup=build_kb_to_edit_one_reminder(),
    )
