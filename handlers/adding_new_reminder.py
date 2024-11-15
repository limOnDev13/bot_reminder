"""
Модуль с хэндлерами для пользователей с обычным статусом,
например, для тех, кто запустил бота в первый раз.
"""

from datetime import date, datetime, timedelta
from typing import Any

from aiogram import F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.types.message import ContentType
from asyncpg import Record

from database import DataBaseClass, TodayRemindersClass, add_new_user, add_reminder
from filters import InputIsDate, InputIsTime
from keyboards import build_kb_with_dates, build_kb_with_one_cancel
from lexicon import LEXICON_RU
from states import FSMReminderCreating

router: Router = Router()


# Обработка команды /start
@router.message(CommandStart())
async def process_start_command(message: Message, database: DataBaseClass):
    await message.answer(text=LEXICON_RU["start"])
    await add_new_user(connector=database, user_id=message.from_user.id)


# Обработка команды /help
@router.message(Command(commands=["help"]))
async def process_help_command(message: Message):
    await message.answer(text=LEXICON_RU["help"])


# Обработка сообщения. Начинаем процесс сохранения напоминания
@router.message(StateFilter(default_state))
async def start_saving_process(message: Message, state: FSMContext):
    # Просим ввести дату напоминания
    await message.answer(
        text=LEXICON_RU["date_msg"], reply_markup=build_kb_with_dates()
    )
    # Если пользователь прислал текстовое сообщение
    if message.content_type is ContentType.TEXT:
        # Сохраняем в оперативной памяти введенный текст
        await state.update_data(
            text=message.text, file_id=None, file_unique_id=None, msg_type="text"
        )
    # Если пользователь прислал любой другой тип
    elif message.content_type is ContentType.PHOTO:
        await state.update_data(
            text=message.caption,
            file_id=message.photo[-1].file_id,
            file_unique_id=message.photo[-1].file_unique_id,
            msg_type="photo",
        )
    elif message.content_type is ContentType.VIDEO_NOTE:
        await state.update_data(
            text=None,
            file_id=message.video_note.file_id,
            file_unique_id=message.video_note.file_unique_id,
            msg_type="video_note",
        )
    elif message.content_type is ContentType.VOICE:
        await state.update_data(
            text=None,
            file_id=message.voice.file_id,
            file_unique_id=message.voice.file_unique_id,
            msg_type="voice",
        )
    elif message.content_type is ContentType.DOCUMENT:
        await state.update_data(
            text=message.caption,
            file_id=message.document.file_id,
            file_unique_id=message.document.file_unique_id,
            msg_type="document",
        )
    elif message.content_type is ContentType.AUDIO:
        await state.update_data(
            text=message.caption,
            file_id=message.audio.file_id,
            file_unique_id=message.audio.file_unique_id,
            msg_type="audio",
        )
    elif message.content_type is ContentType.VIDEO:
        await state.update_data(
            text=message.caption,
            file_id=message.video.file_id,
            file_unique_id=message.video.file_unique_id,
            msg_type="video",
        )
    # Меням состояние на ввод даты
    await state.set_state(FSMReminderCreating.fill_date)


# Обработка нажатия кнопки ОТМЕНА в не дефолтном состоянии
@router.message(F.text == LEXICON_RU["cancel_bt_text"], ~StateFilter(default_state))
async def cancel_saving_process(message: Message, state: FSMContext):
    # Сообщаем пользователю, что он может начать сохранять напоминание
    await message.answer(
        text=LEXICON_RU["cancel_saving_process"], reply_markup=ReplyKeyboardRemove()
    )
    # Сбрасываем состояние до дефолтного
    await state.clear()


# Проверяем нажатие на кнопки Сегодня и Завтра
@router.message(
    F.text == LEXICON_RU["today_bt_text"] or F.text == LEXICON_RU["tomorrow_bt_text"],
    StateFilter(FSMReminderCreating.fill_date),
)
async def process_today_or_tomorrow_buttons(message: Message, state: FSMContext):
    # Если пользователь выбрал Сегодня
    if message.text == LEXICON_RU["today_bt_text"]:
        selected_date = datetime.today()
    # Если пользователь выбрал Завтра
    else:
        selected_date = datetime.today() + timedelta(days=1)

    # Сохраним дату в оперативной памяти
    await state.update_data(date=selected_date.date())
    # Изменим состояние на ввод времени
    await state.set_state(FSMReminderCreating.fill_time)
    # Попросим ввести время напоминания
    await message.answer(
        text=LEXICON_RU["time_msg"], reply_markup=build_kb_with_one_cancel()
    )


# Если юзер находится в состоянии ввода даты и вел ее в правильном
# формате, проверяем, не прошла ли выбранная дата. Если нет -
# продолжаем процесс сохранения напоминания. Если да - просим ввести
# валидную дату
@router.message(StateFilter(FSMReminderCreating.fill_date), InputIsDate())
async def process_input_date(
    message: Message, valid_date: bool | datetime, state: FSMContext
):
    # Если введенная дата еще не прошла
    if valid_date:
        # Сохраним дату в оперативной памяти
        await state.update_data(date=valid_date.date())
        # Изменим состояние на ввод времени
        await state.set_state(FSMReminderCreating.fill_time)
        # Попросим пользователя ввести время напоминания
        await message.answer(
            text=LEXICON_RU["time_msg"], reply_markup=build_kb_with_one_cancel()
        )
    # Если введенная дата прошла
    else:
        # Сообщим пользователю, что введенная дата прошла и попросим ввести ее заново
        await message.answer(text=LEXICON_RU["past_date"])


# Этот хэндлер будет отлавливать все остальные апдейты
# в состоянии fill_date
@router.message(StateFilter(FSMReminderCreating.fill_date))
async def process_wrong_input_date(message: Message):
    # Просим пользователя ввести дату в правильном формате
    await message.answer(text=LEXICON_RU["wrong_format_date_msg"])


# Хэндлер, реагирующий на правильно введенное время (сам формат правилен)
@router.message(StateFilter(FSMReminderCreating.fill_time), InputIsTime())
async def process_input_time(
    message: Message,
    selected_more_current: bool,
    valid_time: datetime,
    state: FSMContext,
    database: DataBaseClass,
    today_reminders: TodayRemindersClass,
):
    current_date: date = datetime.today().date()
    # Получим ранее введенную дату
    saved_data: dict[str, Any] = await state.get_data()
    saved_date: date = saved_data["date"]

    # Если выбрана сегодняшняя дата и выбранное время больше текущего или
    # если выбрана дата больше сегодняшней
    if ((saved_date == current_date) and selected_more_current) or (
        saved_date > current_date
    ):
        # Получим ранее введенный текст
        saved_text: str = saved_data["text"]
        saved_file_id: str = saved_data["file_id"]
        saved_file_unique_id: str = saved_data["file_unique_id"]
        saved_msg_type: str = saved_data["msg_type"]

        # Добавим новую заметку в базу данных
        reminder: Record = await add_reminder(
            connector=database,
            user_id=message.from_user.id,
            reminder_date=saved_date,
            reminder_time=valid_time.time(),
            reminder_text=saved_text,
            file_id=saved_file_id,
            file_unique_id=saved_file_unique_id,
            msg_type=saved_msg_type,
        )
        # Если была выбрана сегодняшняя дата
        if saved_date == current_date:
            # Добавим заметку в список сегодняшних заметок
            today_reminders.push([reminder])

        # Сообщаем пользователю, что заметка успешно сохранена
        await message.answer(
            text=LEXICON_RU["successful_saving"], reply_markup=ReplyKeyboardRemove()
        )

        # Очищаем оперативную память
        await state.clear()
    # Если пользователь ввел время, которое уже прошло
    else:
        # Сообщаем пользователю, что он ввел время которое уже прошло
        await message.answer(text=LEXICON_RU["past_time"])


# Хэндлер, реагирующий на все остальные месседжи в состоянии написания времени
@router.message(StateFilter(FSMReminderCreating.fill_time))
async def process_input_wrong_time_format(message: Message):
    # Сообщаем пользователю, что он ввел время в неправильном формате
    await message.answer(text=LEXICON_RU["wrong_format_time_msg"])
