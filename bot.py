import asyncio
import logging

import asyncpg
from asyncpg.pool import Pool
from aiogram import Bot, Dispatcher, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types.message import ContentType
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from keyboards import set_main_menu
from config_data import Config, load_config
from handlers import (show_some_reminders,
                      edit_list_reminders, show_one_reminder,
                      edit_one_reminder, adding_new_reminder)
from handlers.buy_premium import order, send_pre_checkout_query, successful_payment
from middlewares import DataBaseMiddleware, SchedulerMiddleware,\
    TodayRemindersMiddleware, ProviderTokenMiddleware
from middlewares.reminders_limits import RemindersLimits
from database import TodayRemindersClass
from services import plan_date_save_today_reminders, plan_cron_save_today_reminders


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
    pool_connect: Pool = await asyncpg.create_pool(host=config.con_pool.db.host,
                                                   port=config.con_pool.db.port,
                                                   database=config.con_pool.db.db_name,
                                                   user=config.con_pool.user.user,
                                                   password=config.con_pool.user.password
                                                   )

    scheduler: AsyncIOScheduler = AsyncIOScheduler()

    today_reminders: TodayRemindersClass = TodayRemindersClass(
        scheduler=scheduler,
        bot=bot,
        pool=pool_connect
    )
    plan_date_save_today_reminders(scheduler=scheduler, pool=pool_connect,
                                   today_reminders=today_reminders)
    plan_cron_save_today_reminders(scheduler=scheduler, pool=pool_connect,
                                   today_reminders=today_reminders)

    scheduler.start()

    # Регистрируем мидлвари
    dp.update.middleware.register(ProviderTokenMiddleware(config.prov_token))
    dp.update.middleware.register(DataBaseMiddleware(pool_connect))
    dp.update.middleware.register(SchedulerMiddleware(scheduler))
    dp.update.middleware.register(TodayRemindersMiddleware(today_reminders))

    # Регистрируем хэндлеры для оплаты премиума
    dp.message.register(order, Command(commands=['premium']))
    dp.pre_checkout_query.register(send_pre_checkout_query)
    dp.message.register(successful_payment,
                        F.content_type.in_({ContentType.SUCCESSFUL_PAYMENT}))

    # Регистрируем роутеры
    dp.include_router(show_some_reminders.router)
    dp.include_router(edit_list_reminders.router)
    dp.include_router(show_one_reminder.router)
    dp.include_router(edit_one_reminder.router)
    dp.include_router(adding_new_reminder.router)

    # Зарегистрируем мидлварь для adding_new_reminder.router
    adding_new_reminder.router.message.outer_middleware(RemindersLimits(pool=pool_connect))

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
