"""
Пакет с модулями, в которых хранятся и/или динамически формируются
клавиатуры, отправляемые пользователем ботом, в процессе взаимодействия
"""
from .set_menu import set_main_menu
from .keyboard_utils import (build_kb_with_dates, build_kb_with_one_cancel,
                             build_kb_to_choose_date_to_show, build_kb_with_reminders,
                             build_kb_with_reminder, build_kb_to_edit_one_reminder,
                             kb_with_cancel_button, build_kb_to_edit_list_reminders)

