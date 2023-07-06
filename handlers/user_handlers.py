"""
Модуль с хэндлерами для пользователей с обычным статусом,
например, для тех, кто запустил бота в первый раз.
"""
from aiogram import Router
from aiogram.filters import Command, CommandStart, Text, StateFilter, or_f
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from datetime import date, timedelta, datetime

from keyboards import build_kb_with_dates, build_kb_with_one_cancel
from lexicon import LEXICON_RU
from states import FSMReminderCreating
from database import DataBaseClass, add_new_user, add_reminder
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
    await message.answer(text=LEXICON_RU['date_msg'],
                         reply_markup=build_kb_with_dates())
    await state.update_data(text=message.text)
    await state.set_state(FSMReminderCreating.fill_date)


# Обработка нажатия кнопки ОТМЕНА в не дефолтном состоянии
@router.message(Text(text=LEXICON_RU['cancel_bt_text']),
                ~StateFilter(default_state))
async def cancel_saving_process(message: Message,
                                state: FSMContext):
    await message.answer(text=LEXICON_RU['cancel_saving_process'],
                         reply_markup=ReplyKeyboardRemove())
    await state.set_state(default_state)


# Проверяем нажатие на кнопки Сегодня и Завтра
@router.message(StateFilter(FSMReminderCreating.fill_date),
                Text(text=[LEXICON_RU['today_bt_text'],
                           LEXICON_RU['tomorrow_bt_text']]))
async def process_today_or_tomorrow_buttons(message: Message,
                                            state: FSMContext):
    if message.text == LEXICON_RU['today_bt_text']:
        selected_date = datetime.today()
    else:
        selected_date = datetime.today() + timedelta(days=1)

    await state.update_data(date=selected_date.date())
    await state.set_state(FSMReminderCreating.fill_time)
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
    if valid_date:
        await state.update_data(date=valid_date.date())
        await state.set_state(FSMReminderCreating.fill_time)
        await message.answer(text=LEXICON_RU['time_msg'],
                             reply_markup=build_kb_with_one_cancel())
    else:
        await message.answer(text=LEXICON_RU['past_date'])


# Этот хэндлер будет отлавливать все остальные апдейты
# в состоянии fill_date
@router.message(StateFilter(FSMReminderCreating.fill_date))
async def process_wrong_input_date(message: Message):
    await message.answer(text=LEXICON_RU['wrong_format_date_msg'])


# Хэндлер, реагирующий на правильно введенное время (сам формат правилен)
@router.message(StateFilter(FSMReminderCreating.fill_time),
                InputIsTime())
async def process_input_time(message: Message,
                             selected_more_current: bool,
                             valid_time: datetime,
                             state: FSMContext,
                             database: DataBaseClass):
    current_date: date = datetime.today().date()

    saved_date = await state.get_data()

    if ((saved_date['date'] == current_date) and selected_more_current) or \
            (saved_date['date'] > current_date):
        await state.update_data(time=valid_time.time())

        reminder_info = await state.get_data()
        await add_reminder(
            connector=database,
            user_id=message.from_user.id,
            reminder_date=reminder_info['date'],
            reminder_time=reminder_info['time'],
            reminder_text=reminder_info['text']
        )

        await message.answer(text=LEXICON_RU['successful_saving'],
                             reply_markup=ReplyKeyboardRemove())
        await state.clear()
    else:
        await message.answer(text=LEXICON_RU['past_time'])


# Хэндлер, реагирующий на все остальные месседжи в состоянии написания времени
@router.message(StateFilter(FSMReminderCreating.fill_time))
async def process_input_wrong_time_format(message: Message):
    await message.answer(text=LEXICON_RU['wrong_format_time_msg'])
