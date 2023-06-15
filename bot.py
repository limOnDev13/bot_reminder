from aiogram import Bot, Dispatcher
from keyboards import set_main_menu
from config_data import Config, load_config


async def main():
    config: Config = load_config(None)
    bot: Bot = Bot(token=config.tg_bot.token,
                   parse_mode='HTML')
    dp: Dispatcher = Dispatcher()

    await set_main_menu(bot)
