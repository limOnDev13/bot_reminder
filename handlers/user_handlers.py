"""
Модуль с хэндлерами для пользователей с обычным статусом,
например, для тех, кто запустил бота в первый раз.
"""
from aiogram import Router
from aiogram.filters import Command, CommandStart, Text
from aiogram.types import Message, CallbackQuery

import keyboards
from lexicon import LEXICON_RU
import services
from models import models


router: Router = Router()


@router.message(CommandStart())
async def process_start_command(message: Message):
    await message.answer(text=LEXICON_RU['start'])


@router.message(Command(commands=['help']))
async def process_help_command(message: Message):
    await message.answer(text=LEXICON_RU['help'])


@router.message(Command(commands=['reminders']))
async def process_reminders_command(message: Message):
    pass



