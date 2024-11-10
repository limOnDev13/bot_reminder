from aiogram import Bot
from aiogram.types import LabeledPrice, Message, PreCheckoutQuery

from database.connection_pool import DataBaseClass
from database.methods import set_premium
from lexicon import LEXICON_RU

price_premium: LabeledPrice = LabeledPrice(
    label=LEXICON_RU["label_premium"], amount=99999  # Указано в копейках
)
discount_amount: LabeledPrice = LabeledPrice(
    label=LEXICON_RU["label_discount"], amount=-99
)


async def order(message: Message, bot: Bot, provider_token: str):
    await bot.send_invoice(
        chat_id=message.chat.id,
        title=LEXICON_RU["payment_title"],
        description=LEXICON_RU["payment_description"],
        payload=LEXICON_RU["payment_payload"],
        provider_token=provider_token,
        currency="rub",
        prices=[price_premium, discount_amount],
        max_tip_amount=5000,  # Максимальный размер чаевых
        # Предлагаемые чаевые (максимум только 4)
        suggested_tip_amounts=[1000, 2000, 3000, 4000],
        # если стартовый параметр пустой, то при пересылке счета оплатить может
        # кто угодно, если не пустой - при пересылке счета будет присылаться ссылка
        # на бота
        start_parameter="limon_fresh",
        # Необходимая инфа для провайдера
        provider_data=None,
        # Ссылка на фото, которое отобразиться в счете
        photo_url="https://storage.easyx.ru/"
        "images/easydonate/products/"
        "HzllzSdR23OHvPXxF3YCrkGwdR4IgQ29.jpg",
        # Размер фото
        photo_size=100,
        photo_width=450,
        photo_height=450,
        # Если нужно полное имя пользователя
        need_name=True,
        # Если нужен полное телефон пользователя
        need_phone_number=True,
        # Если нужен email пользователя
        need_email=True,
        # Если есть доставка
        need_shipping_address=False,
        # Если нужно передать данные провайдеру
        send_phone_number_to_provider=False,
        send_email_to_provider=False,
        # Если конечная цена зависит от доставки
        is_flexible=False,
        # Если необходимо доставить сообщение без звука
        disable_notification=False,
        # Если нужно защитить контент от пересылки, копирования и т.п.
        protect_content=True,
        # Если нужно отправить в ответ на сообщение пользователя - ввести id
        reply_to_message_id=None,
        # Если хотите отправить счет на оплату, даже если цитируемое сообщение
        # не найдено
        allow_sending_without_reply=True,
        reply_markup=None,
        request_timeout=15,
    )


async def send_pre_checkout_query(pre_checkout_query: PreCheckoutQuery, bot: Bot):
    # Если мы готовы выслать продукт, то ok = True
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


async def successful_payment(message: Message, database: DataBaseClass):
    msg: str = (
        LEXICON_RU["successful_payment_msg"]
        + f"{message.successful_payment.total_amount // 100} "
        f"{message.successful_payment.currency}."
    )
    await message.answer(msg)
    await set_premium(connector=database, user_id=message.from_user.id)
