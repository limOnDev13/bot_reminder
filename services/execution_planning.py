"""
Модуль, который отвечает за планирование выполнения задач из бизнес-логики
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from asyncpg.pool import Pool
from aiogram import Bot
from datetime import datetime, timedelta

from . import services
from database import TodayRemindersClass


def planning_get_today_reminders(scheduler: AsyncIOScheduler,
                                 pool_connect: Pool,
                                 today_reminders: TodayRemindersClass):
    scheduler.add_job(services.save_list_today_reminders, trigger='cron',
                      hour=0, minute=0,
                      start_date=datetime.now() + timedelta(seconds=10),
                      kwargs={'pool': pool_connect,
                              'today_reminders': today_reminders})


def planning_send_appropriate_reminder(scheduler: AsyncIOScheduler,
                                       bot: Bot,
                                       pool_connect: Pool,
                                       today_reminders: TodayRemindersClass):
    scheduler.add_job(services.send_appropriate_reminder, trigger='date',
                      run_date=today_reminders.get_near_datetime(),
                      kwargs={'bot': bot,
                              'pool': pool_connect,
                              'today_reminders_list': today_reminders})
