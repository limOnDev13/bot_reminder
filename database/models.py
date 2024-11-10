from datetime import date, time
from typing import Optional

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Text, Time
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class User(Base):
    __tablename__ = "Users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    premium: Mapped[bool] = mapped_column(Boolean, nullable=False, default=0)
    num_reminders: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Reminders(Base):
    __tablename__ = "Reminders"

    reminder_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("Users.user_id"))
    reminder_date: Mapped[date] = mapped_column(Date, nullable=False)
    reminder_time: Mapped[time] = mapped_column(Time, nullable=False)
    reminder_text: Mapped[str] = mapped_column(Text)
    last_reminder: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    file_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default=None)
    file_unique_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default=None)
    msg_type: Mapped[str] = mapped_column(Text, nullable=False, default="text")
