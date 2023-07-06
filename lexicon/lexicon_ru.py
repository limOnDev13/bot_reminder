"""
Модуль со словарем соответствий данных текстам на рус языке.
"""
LEXICON_COMMANDS_RU: dict[str, str] = {
    '/help': 'Справка о возможностях бота',
    '/reminders': 'Вывести все напоминания',
    '/today': 'Вывести напоминания на сегодня',
    '/tomorrow': 'Вывести напоминания на завтра'
}

LEXICON_RU: dict[str, str] = {
    'start': 'Приветствую! Я бот - напоминалка, могу сохранять ваши сообщения на указанные вами даты и время.\n'
             'Для более подробной справки отправьте команду /help.\n'
             'Для начала работы отправьте мне любое сообщение.',
    'help': 'Я бот - напоминалка. Отправьте мне сообщение, и если формат сообщения позволит его сохранить в базе'
            ' данных, я попрошу вас указать сначала дату в формате ДД ММ ГГГГ, а после - время в формате ЧЧ ММ. После,'
            ' когда наступит указанное вами дата и время, я перешлю ваше сообщение.\n'
            'Вам доступны следующие команды:\n'
            '/reminds - я попрошу вас ввести дату в формате ДД.ММ.ГГГГ, и после выведу список всех ваших'
            ' заметок на выбранную дату;\n'
            '/today - я выведу список всех оставшихся на сегодня заметок;\n'
            '/tomorrow - я выведу список всех заметок на завтра;\n'
            'Любой список заметок, как и сами заметки, можно в любой момент отредактировать.\n'
            '/premium - у обычного пользователя есть пара ограничений. Он может сохранить не более 50 заметок,'
            ' и только в виде текста. Если же вы хотите снять всякие ограничения и закинуть моему автору на чай,'
            ' отправьте мне эту команду;)'
            'Теперь, если хотите сохранить заметку, просто отправьте ее мне.',
    'date_msg': 'Введите дату, когда вам отправить напоминание, в формате ДД.ММ.ГГГГ (если отправите в формате ДД ММ,'
                ' сохраню на этот год, если просто ДД, то на этот месяц):',
    'today_bt_text': 'Сегодня',
    'tomorrow_bt_text': 'Завтра',
    'today_msg': 'Вот список напоминаний, оставшихся на сегодня:',
    'tomorrow_msg': 'Вот список напоминаний на завтра:',
    'wrong_format_date_msg': 'Вы ввели несуществующую дату или дату в неправильном формате.\n'
                             'Отправьте мне дату в форматах ДД.ММ.ГГГГ или ДД.ММ'
                             ' или просто ДД. Также нельзя выбрать прошедшую дату.\n'
                             'Чтобы прервать сохранение заметки, нажмите на кнопку ОТМЕНА.',
    'past_date': 'Выбранная дата уже прошла.\n'
                 ' Пожалуйста, отправьте мне дату в правильном формате (ДД.ММ.ГГГГ или ДД.ММ или ДД) или'
                 ' отмените сохранение заметки, нажав на кнопку ОТМЕНА',
    'time_msg': 'Введите время в формате ЧЧ:ММ',
    'past_time': 'Выбранное вами время уже прошло. Пожалуйста, выберете время, которое еще не прошло.',
    'wrong_format_time_msg': 'Вы ввели время в неправильном формате.\nОтправьте мне время в формате ЧЧ ММ. Также,'
                             ' если ты выбрал сегодняшний день, нельзя выбрать прошедшее время.',
    'successful_saving': 'Заметка успешно сохранена!',
    'failed save': 'Что-то пошло не так, заметку сохранить не удалось:(',
    'reminders': 'Пожалуйста, введите дату, заметки на которую вы хотите просмотреть, в формате ДД.ММ.ГГГГ',
    'previous_page': '<<',
    'previous_page_cb': 'previous_page_cb',
    'next_page': '>>',
    'next_page_cb': 'next_page_cb',
    'cancel_bt_text': 'ОТМЕНА',
    'cancel_saving_process': 'Напоминание не сохранено.\n'
                             'Чтобы сохранить новое напоминание, просто'
                             'отправьте мне любое сообщение.'
                             ' (пока только текстовое)',
    'edit': '❌ РЕДАКТИРОВАТЬ',
    'edit_cb': 'edit_cb',
    'cancel_view_msg': 'Чтобы сохранить заметку просто напишите мне;)',
    'cancel_cb': 'cancel_cb',
    'all': 'Все',
    'back_msg': 'НАЗАД',
    'back_cb': 'back_cb',
    'sec_please': 'Секунду, взламываю Пентагон, чтобы просмотреть базу данных ООН.\n'
                  'И... Готово!',
    'reminders_on_chosen_date_msg': 'Вот список заметок на ',
    'enter_new_reminder': 'НОВАЯ ЗАМЕТКА',
    'enter_new_reminder_cb': 'new_reminder',
    'back_to_reminders_menu_cb': 'back_to_reminders_menu_cb',
    'delete_reminder_msg': 'УДАЛИТЬ',
    'delete_reminder_cb': 'delete_reminder_cb',
    'reminder_was_deleted': 'Заметка была удалена.',
    'what_edit': 'Что вы хотите изменить в напоминании?',
    'change_text_msg': 'Текст',
    'change_text_cb': 'change_text_cb',
    'change_date_msg': 'Дату',
    'change_date_cb': 'change_date_cb',
    'change_time_msg': 'Время',
    'change_time_cb': 'change_time_cb',
    'complete_edit_msg': 'ГОТОВО',
    'complete_edit_cb': 'complete_edit_cb',
    'new_reminder_text': 'Введите новый текст',
    'done': '\nГотово!\n',
    'new_reminder_date': 'Введите новую дату в формате'
                         ' ДД.ММ.ГГГГ (или ДД.ММ, или ДД)',
    'new_reminder_time': 'Введите новое время в формате ЧЧ:ММ',
    'wrong_format': 'Данные введены в неверном формате.'
                    ' Пожалуйста, введите корректные данные',
    'editing_complete_msg': 'Изменения сохранены!\nЕсли хотите сохранить новую'
                            ' заметку, просто напишите мне;)',
    'view_all_reminders': 'Вот список всех ваших заметок',
    'number_showed_reminders': 'Всего заметок показано: ',
    'what_reminders_delete': 'Нажмите на заметки, которые хотите удалить.',
    'not_understand': 'Извините, я вас не понимаю 😕\n'
}
