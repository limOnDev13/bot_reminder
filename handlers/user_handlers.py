"""
Модуль с хэндлерами для пользователей с обычным статусом,
например, для тех, кто запустил бота в первый раз.
"""
from aiogram import Router, F
from aiogram.filters import (Command, CommandStart, Text, StateFilter,
                             or_f)
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.fsm.storage.memory import MemoryStorage
from datetime import date, timedelta

from keyboards import build_kb_with_dates
from lexicon import LEXICON_RU
from states import FSMReminderCreating
import services
from database import DataBaseClass, add_new_user, add_reminder
from filters import InputIsDate


router: Router = Router()

storage: MemoryStorage = MemoryStorage()


# Обработка команды /start
@router.message(CommandStart())
async def process_start_command(message: Message, database: DataBaseClass):
    await message.answer(text=LEXICON_RU['start'])
    await add_new_user(connector=database, user_id=message.from_user.id)


# Обработка команды /help
@router.message(Command(commands=['help']))
async def process_help_command(message: Message):
    await message.answer(text=LEXICON_RU['help'])


# Обработка команды /reminders (нужно доделать)
@router.message(Command(commands=['reminders']))
async def process_reminders_command(message: Message, database: DataBaseClass):
    pass


# Обработка текстового сообщения. Начинаем процесс сохранения напоминания
@router.message(StateFilter(default_state))
async def start_saving_process(message: Message, state: FSMContext):
    await message.answer(text=LEXICON_RU['date_msg'],
                         reply_markup=build_kb_with_dates())
    await state.set_state(FSMReminderCreating.fill_date)


# Обработка нажатия кнопки ОТМЕНА в не дефолтном состоянии
@router.message(Text(text=LEXICON_RU['cancel_bt_text']),
                ~StateFilter(default_state))
async def cancel_saving_process(message: Message,
                                state: FSMContext):
    await message.answer(text=LEXICON_RU['cancel_saving_process'],
                         reply_markup=ReplyKeyboardRemove())
    await state.set_state(default_state)


# Метод, который приводит дату к правильному для Postgresql формату
def right_date_formate(selected_date: date) -> str:
    result = str(selected_date.year) + '-' + \
             str(selected_date.month) + '-' + \
             str(selected_date.day)

    return result


@router.message(StateFilter(FSMReminderCreating.fill_date),
                Text(text=[LEXICON_RU['today_bt_text'],
                           LEXICON_RU['tomorrow_bt_text']]))
async def process_today_or_tomorrow_buttons(message: Message,
                                            state: FSMContext):
    if message.text == LEXICON_RU['today_bt_text']:
        selected_date = right_date_formate(date.today())
    else:
        selected_date = right_date_formate(date.today() +
                                           timedelta(days=1))

    await state.update_data(date=selected_date)
    await state.set_state(FSMReminderCreating.fill_time)
    await message.answer(text=LEXICON_RU['time_msg'],
                         reply_markup=ReplyKeyboardRemove())


# Если юзер находится в состоянии ввода даты и вел ее в правильном
# формате, проверяем, не прошла ли выбранная дата. Если нет -
# продолжаем процесс сохранения напоминания. Если да - просим ввести
# валидную дату
@router.message(StateFilter(FSMReminderCreating.fill_date),
                InputIsDate())
async def process_input_date(message: Message,
                             valid_date: bool | str,
                             state: FSMContext):
    if valid_date:
        await state.update_data(date=valid_date)
        await state.set_state(FSMReminderCreating.fill_time)
        await message.answer(text=LEXICON_RU['time_msg'],
                             reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer(text=LEXICON_RU['past_date'])


# Этот хэндлер будет отлавливать все остальные апдейты
# в состоянии fill_date
@router.message(StateFilter(FSMReminderCreating.fill_date))
async def process_wrong_input_date(message: Message):
    await message.answer(text=LEXICON_RU['wrong_format_date_msg'])
