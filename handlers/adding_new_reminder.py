"""
Модуль с хэндлерами для пользователей с обычным статусом,
например, для тех, кто запустил бота в первый раз.
"""
from aiogram import Router
from aiogram.filters import Command, CommandStart, Text, StateFilter
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from datetime import date, timedelta, datetime
from typing import Any
from asyncpg import Record

from keyboards import build_kb_with_dates, build_kb_with_one_cancel
from lexicon import LEXICON_RU
from states import FSMReminderCreating
from database import DataBaseClass, add_new_user, add_reminder, TodayRemindersClass
from filters import InputIsDate, InputIsTime


router: Router = Router()


# Обработка команды /start
@router.message(CommandStart())
async def process_start_command(message: Message, database: DataBaseClass):
    await message.answer(text=LEXICON_RU['start'])
    await add_new_user(connector=database, user_id=message.from_user.id)


# Обработка команды /help
@router.message(Command(commands=['help']))
async def process_help_command(message: Message):
    await message.answer(text=LEXICON_RU['help'])


# Обработка текстового сообщения. Начинаем процесс сохранения напоминания
@router.message(StateFilter(default_state))
async def start_saving_process(message: Message, state: FSMContext):
    # Просим ввести дату напоминания
    await message.answer(text=LEXICON_RU['date_msg'],
                         reply_markup=build_kb_with_dates())
    # Сохраняем в оперативной памяти введенный текст
    await state.update_data(text=message.text)
    # Меням состояние на ввод даты
    await state.set_state(FSMReminderCreating.fill_date)


# Обработка нажатия кнопки ОТМЕНА в не дефолтном состоянии
@router.message(Text(text=LEXICON_RU['cancel_bt_text']),
                ~StateFilter(default_state))
async def cancel_saving_process(message: Message,
                                state: FSMContext):
    # Сообщаем пользователю, что он может начать сохранять напоминание
    await message.answer(text=LEXICON_RU['cancel_saving_process'],
                         reply_markup=ReplyKeyboardRemove())
    # Сбрасываем состояние до дефолтного
    await state.clear()


# Проверяем нажатие на кнопки Сегодня и Завтра
@router.message(StateFilter(FSMReminderCreating.fill_date),
                Text(text=[LEXICON_RU['today_bt_text'],
                           LEXICON_RU['tomorrow_bt_text']]))
async def process_today_or_tomorrow_buttons(message: Message,
                                            state: FSMContext):
    # Если пользователь выбрал Сегодня
    if message.text == LEXICON_RU['today_bt_text']:
        selected_date = datetime.today()
    # Если пользователь выбрал Завтра
    else:
        selected_date = datetime.today() + timedelta(days=1)

    # Сохраним дату в оперативной памяти
    await state.update_data(date=selected_date.date())
    # Изменим состояние на ввод времени
    await state.set_state(FSMReminderCreating.fill_time)
    # Попросим ввести время напоминания
    await message.answer(text=LEXICON_RU['time_msg'],
                         reply_markup=build_kb_with_one_cancel())


# Если юзер находится в состоянии ввода даты и вел ее в правильном
# формате, проверяем, не прошла ли выбранная дата. Если нет -
# продолжаем процесс сохранения напоминания. Если да - просим ввести
# валидную дату
@router.message(StateFilter(FSMReminderCreating.fill_date),
                InputIsDate())
async def process_input_date(message: Message,
                             valid_date: bool | datetime,
                             state: FSMContext):
    # Если введенная дата еще не прошла
    if valid_date:
        # Сохраним дату в оперативной памяти
        await state.update_data(date=valid_date.date())
        # Изменим состояние на ввод времени
        await state.set_state(FSMReminderCreating.fill_time)
        # Попросим пользователя ввести время напоминания
        await message.answer(text=LEXICON_RU['time_msg'],
                             reply_markup=build_kb_with_one_cancel())
    # Если введенная дата прошла
    else:
        # Сообщим пользователю, что введенная дата прошла и попросим ввести ее заново
        await message.answer(text=LEXICON_RU['past_date'])


# Этот хэндлер будет отлавливать все остальные апдейты
# в состоянии fill_date
@router.message(StateFilter(FSMReminderCreating.fill_date))
async def process_wrong_input_date(message: Message):
    # Просим пользователя ввести дату в правильном формате
    await message.answer(text=LEXICON_RU['wrong_format_date_msg'])


# Хэндлер, реагирующий на правильно введенное время (сам формат правилен)
@router.message(StateFilter(FSMReminderCreating.fill_time),
                InputIsTime())
async def process_input_time(message: Message,
                             selected_more_current: bool,
                             valid_time: datetime,
                             state: FSMContext,
                             database: DataBaseClass,
                             today_reminders: TodayRemindersClass):
    current_date: date = datetime.today().date()
    # Получим ранее введенную дату
    saved_data: dict[str, Any] = await state.get_data()
    saved_date: date = saved_data['date']

    # Если выбрана сегодняшняя дата и выбранное время больше текущего или
    # если выбрана дата больше сегодняшней
    if ((saved_date == current_date) and selected_more_current) or \
            (saved_date > current_date):
        # Получим ранее введенный текст
        saved_text: str = saved_data['text']

        # Добавим новую заметку в базу данных
        reminder: Record = await add_reminder(
            connector=database,
            user_id=message.from_user.id,
            reminder_date=saved_date,
            reminder_time=valid_time.time(),
            reminder_text=saved_text
        )
        # Если была выбрана сегодняшняя дата
        if saved_date == current_date:
            # Добавим заметку в список сегодняшних заметок
            today_reminders.push([reminder])

        # Сообщаем пользователю, что заметка успешно сохранена
        await message.answer(text=LEXICON_RU['successful_saving'],
                             reply_markup=ReplyKeyboardRemove())
        # Очищаем оперативную память
        await state.clear()
    # Если пользователь ввел время, которое уже прошло
    else:
        # Сообщаем пользователю, что он ввел время которое уже прошло
        await message.answer(text=LEXICON_RU['past_time'])


# Хэндлер, реагирующий на все остальные месседжи в состоянии написания времени
@router.message(StateFilter(FSMReminderCreating.fill_time))
async def process_input_wrong_time_format(message: Message):
    # Сообщаем пользователю, что он ввел время в неправильном формате
    await message.answer(text=LEXICON_RU['wrong_format_time_msg'])
