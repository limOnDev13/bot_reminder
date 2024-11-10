"""
Модуль с утилитами - вспомогательными скриптами для работы бота
"""

from datetime import date, time

from aiogram import Bot


def assemble_full_reminder_text(
    reminder_text: str | None, reminder_date: date, reminder_time: time
) -> str:
    result_reminder_text: str

    if reminder_text is not None:
        result_reminder_text = (
            reminder_text
            + "\nДата: "
            + reminder_date.strftime("%d.%m.%Y")
            + "\nВремя: "
            + reminder_time.strftime("%H:%M")
            + "\n"
        )
    else:
        result_reminder_text = (
            "Дата: "
            + reminder_date.strftime("%d.%m.%Y")
            + "\nВремя: "
            + reminder_time.strftime("%H:%M")
            + "\n"
        )

    return result_reminder_text


async def send_not_text(
    msg_type: str, user_id: int, file_id: str, reminder_text: str
) -> str | None:
    bot: Bot = Bot.get_current()
    caption: str | None = None

    if msg_type == "voice":
        await bot.send_voice(user_id, voice=file_id)
    elif msg_type == "video_note":
        await bot.send_video_note(user_id, video_note=file_id)
    else:
        caption = reminder_text

        if msg_type == "video":
            await bot.send_video(user_id, video=file_id)
        elif msg_type == "photo":
            await bot.send_photo(user_id, photo=file_id)
        elif msg_type == "audio":
            await bot.send_audio(user_id, audio=file_id)
        elif msg_type == "document":
            await bot.send_document(user_id, document=file_id)

    return caption
