import asyncio
import logging

import asyncpg
from aiogram import Bot, Dispatcher
from keyboards import set_main_menu
from config_data import Config, load_config
from handlers import other_handlers, user_handlers
from utils import DataBaseMiddleware


logger = logging.getLogger(__name__)


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(filename)s:%(lineno)d #%(levelname)-8s '
               '[%(asctime)s] - %(name)s - %(message)s'
    )

    logger.info('Starting bot')

    config: Config = load_config(None)
    bot: Bot = Bot(token=config.tg_bot.token,
                   parse_mode='HTML')
    dp: Dispatcher = Dispatcher()

    await set_main_menu(bot)

    pool_connect = await asyncpg.create_pool(host=config.con_pool.db.host,
                                             port=config.con_pool.db.port,
                                             database=config.con_pool.db.db_name,
                                             user=config.con_pool.user.user,
                                             password=config.con_pool.user.password
                                             )
    dp.message.register(DataBaseMiddleware(pool_connect))

    dp.include_router(user_handlers.router)
    dp.include_router(other_handlers.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
