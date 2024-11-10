import asyncio
import logging

import asyncpg
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types.message import ContentType
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from asyncpg.pool import Pool

import database.models
from config_data import Config, load_config
from database import TodayRemindersClass
from database.database import Base, engine
from handlers import (
    adding_new_reminder,
    edit_list_reminders,
    edit_one_reminder,
    show_one_reminder,
    show_some_reminders,
)
from handlers.buy_premium import order, send_pre_checkout_query, successful_payment
from keyboards import set_main_menu
from middlewares import (
    DataBaseMiddleware,
    ProviderTokenMiddleware,
    SchedulerMiddleware,
    TodayRemindersMiddleware,
)
from middlewares.reminders_limits import RemindersLimits
from services import plan_cron_save_today_reminders, plan_date_save_today_reminders

logger = logging.getLogger(__name__)


async def main():
    # Логирование
    logging.basicConfig(
        level=logging.INFO,
        format="%(filename)s:%(lineno)d #%(levelname)-8s "
        "[%(asctime)s] - %(name)s - %(message)s",
    )

    logger.info("Starting bot")

    # Настройка основных параметров бота
    config: Config = load_config(None)
    bot: Bot = Bot(
        token=config.tg_bot.token,
        # parse_mode='HTML'
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    storage: MemoryStorage = MemoryStorage()
    dp: Dispatcher = Dispatcher(storage=storage)

    # Вывод кнопки меню
    await set_main_menu(bot)

    try:
        # сборка метаданных
        async with engine.begin() as conn:
            logger.info("Create db metadata")
            await conn.run_sync(Base.metadata.create_all)

        # Настройка пула подключений к бд
        pool_connect: Pool = await asyncpg.create_pool(
            host=config.con_pool.db.host,
            port=config.con_pool.db.port,
            user=config.con_pool.user.user,
            password=config.con_pool.user.password,
        )

        scheduler: AsyncIOScheduler = AsyncIOScheduler()

        today_reminders: TodayRemindersClass = TodayRemindersClass(
            scheduler=scheduler, bot=bot, pool=pool_connect
        )
        plan_date_save_today_reminders(
            scheduler=scheduler, pool=pool_connect, today_reminders=today_reminders
        )
        plan_cron_save_today_reminders(
            scheduler=scheduler, pool=pool_connect, today_reminders=today_reminders
        )

        scheduler.start()

        # Регистрируем мидлвари
        dp.update.middleware.register(ProviderTokenMiddleware(config.prov_token))
        dp.update.middleware.register(DataBaseMiddleware(pool_connect))
        dp.update.middleware.register(SchedulerMiddleware(scheduler))
        dp.update.middleware.register(TodayRemindersMiddleware(today_reminders))

        # Регистрируем хэндлеры для оплаты премиума
        dp.message.register(order, Command(commands=["premium"]))
        dp.pre_checkout_query.register(send_pre_checkout_query)
        dp.message.register(
            successful_payment, F.content_type.in_({ContentType.SUCCESSFUL_PAYMENT})
        )

        # Регистрируем роутеры
        dp.include_router(show_some_reminders.router)
        dp.include_router(edit_list_reminders.router)
        dp.include_router(show_one_reminder.router)
        dp.include_router(edit_one_reminder.router)
        dp.include_router(adding_new_reminder.router)

        # Зарегистрируем мидлварь для adding_new_reminder.router
        adding_new_reminder.router.message.outer_middleware(
            RemindersLimits(pool=pool_connect)
        )

        await bot.delete_webhook(drop_pending_updates=True)

        logger.info("Start polling")
        await dp.start_polling(bot)
    finally:
        logger.info("Dispose a db engine")
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
