import asyncio
import logging

import asyncpg
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from keyboards import set_main_menu
from config_data import Config, load_config
from handlers import (other_handlers, reminders_editor_handlers,
                      handlers_to_edit_list_reminders, show_one_reminder_handler,
                      edit_one_reminder_handlers, adding_new_reminder)
from middlewares import DataBaseMiddleware, SchedulerMiddleware,\
    TodayRemindersMiddleware
from database import TodayRemindersClass
from services import planning_get_today_reminders, planning_send_appropriate_reminder


logger = logging.getLogger(__name__)


async def main():
    # Логирование
    logging.basicConfig(
        level=logging.INFO,
        format='%(filename)s:%(lineno)d #%(levelname)-8s '
               '[%(asctime)s] - %(name)s - %(message)s'
    )

    logger.info('Starting bot')

    # Настройка основных параметров бота
    config: Config = load_config(None)
    bot: Bot = Bot(token=config.tg_bot.token,
                   parse_mode='HTML')
    storage: MemoryStorage = MemoryStorage()
    dp: Dispatcher = Dispatcher(storage=storage)

    # Вывод кнопки меню
    await set_main_menu(bot)

    # Настройка пула подключений к бд
    pool_connect = await asyncpg.create_pool(host=config.con_pool.db.host,
                                             port=config.con_pool.db.port,
                                             database=config.con_pool.db.db_name,
                                             user=config.con_pool.user.user,
                                             password=config.con_pool.user.password
                                             )
    today_reminders: TodayRemindersClass = TodayRemindersClass()

    scheduler: AsyncIOScheduler = AsyncIOScheduler()
    planning_get_today_reminders(scheduler=scheduler, pool_connect=pool_connect,
                                 today_reminders=today_reminders)
    planning_send_appropriate_reminder(scheduler=scheduler, bot=bot,
                                       pool_connect=pool_connect,
                                       today_reminders=today_reminders)

    scheduler.start()

    # Регистрируем мидлвари
    dp.update.middleware.register(DataBaseMiddleware(pool_connect))
    dp.update.middleware.register(SchedulerMiddleware(scheduler))
    dp.update.middleware.register(TodayRemindersMiddleware(today_reminders))
    # Регистрируем роутеры
    dp.include_router(reminders_editor_handlers.router)
    dp.include_router(handlers_to_edit_list_reminders.router)
    dp.include_router(show_one_reminder_handler.router)
    dp.include_router(edit_one_reminder_handlers.router)
    dp.include_router(adding_new_reminder.router)
    dp.include_router(other_handlers.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
