"""
Модуль с утилитами - вспомогательными скриптами для работы бота
"""
from datetime import date, time


def assemble_full_reminder_text(reminder_text: str | None,
                                reminder_date: date,
                                reminder_time: time) -> str:
    result_reminder_text: str

    if reminder_text is not None:
        result_reminder_text = reminder_text + \
                                    '\nДата: ' + reminder_date.strftime("%d.%m.%Y") + \
                                    '\nВремя: ' + reminder_time.strftime("%H:%M") + '\n'
    else:
        result_reminder_text = 'Дата: ' + reminder_date.strftime("%d.%m.%Y") + \
                               '\nВремя: ' + reminder_time.strftime("%H:%M") + '\n'

    return result_reminder_text
