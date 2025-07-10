import telebot
from telebot.apihelper import ApiTelegramException
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot.types import LabeledPrice
from telebot.types import BotCommand
from dotenv import load_dotenv
import os
import threading
import time
import logging

from utils.Data import ExcelDatabase
from utils.Answer import Message
from utils.Auxilirate import Auxilirate
from utils.XAPI import X3

load_dotenv()
BOT_API=os.getenv("API_KEY")
slon = ExcelDatabase()
x3 = X3()
answer = Message()
help = Auxilirate()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
bot = telebot.TeleBot(BOT_API)



bot.set_my_commands([
    BotCommand("start", "Перезапустить - личный кабинет"),
    BotCommand("buy", "Продлить подписку"),
    BotCommand("support", "Поддержка")
])



# Функция для создания inline-клавиатуры
def create_inline_keyboard(buttons):
    keyboard = InlineKeyboardMarkup()
    
    rows = [
        buttons[:2],   
        buttons[2:4],  
        buttons[4:6],
        buttons[6:]   
    ]
    for row in rows:
        if row:
            keyboard.row(*[InlineKeyboardButton(text=text, callback_data=callback_data) for text, callback_data in row])
    
    return keyboard






@bot.message_handler(commands=['admin'])
def admin(message):
    # Только для администратора с tg_id = 958535601
    if str(message.chat.id) != '958535601':
        return

    # Кнопка «В личный кабинет»
    keyboard = create_inline_keyboard([
        ("👤В личный кабинет", "menu")
    ])

    # Берём из БД всех пользователей
    tg_list = slon.get_all_tg_ids()
    for tg in tg_list:
        # Если до конца подписки осталось меньше 3 дней — продлеваем
        if x3.get_time(str(tg)) < 3:
            x3.update_client(3, str(tg))

            try:
                bot.send_message(
                    tg,
                    text=(
                        "Здравствуйте! 🌿\n"
                        "Если вы пришли к нам с ИИ-практикума — рады вас видеть.\n\n"
                        "🎁Дарим ещё 3 дня доступа, чтобы вам было проще освоиться и начать использовать нейросети.\n\n"
                        "Мы видим, многие пока не подключили VPN — не переживайте, это совсем просто.\n"
                        "Вот здесь подробная инструкция с фото. Займёт 2 минуты.\n\n"
                        "iPhone - https://telegra.ph/Vless---iPhoneiPad-03-04-2\n"
                        "Android - https://telegra.ph/Vless---Android-03-04\n\n"
                        "Чем наш впн лучше бесплатного барахлящего приложения:\n"
                        "1️⃣ Мы не передаём ваши данные третьим лицам\n"
                        "2️⃣ Максимальная скорость — мы не экономим на дешевом оборудовании\n"
                        "3️⃣ Стоимость подписки — меньше чашки кофе, а освоить ИИ — бесценно🙂\n\n"
                        "Если что-то не получится — напишите в поддержку, мы обязательно поможем💬"
                    ),
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            except ApiTelegramException as e:
                # Если бот был заблокирован — пропускаем и отмечаем статус=0
                if e.error_code == 403:
                    slon.update_cell(tg, column_index=5, new_value=0)
                    continue
                # Иные ошибки пробрасываем дальше
                raise







# Обработка команды /start
@bot.message_handler(commands=['start'])
def start(message):
    ms = message.from_user
    if slon.find_row_index(ms.id) is None:
        args = help.get_args(message.text.split(maxsplit=1), ms.id) 
        x3.add_connection(3, ms.id, ms.id)
        slon.add_row(ms.username, ms.id, "standart", args, 0)
        keyboard = create_inline_keyboard([("Далее", "next")])
        bot.send_message(message.chat.id, text=answer.yep(), reply_markup=keyboard, parse_mode="HTML")
    else:
        link = "..."
        flag = "🔴 Ключ неактивен"
        client_time = x3.get_time(str(message.chat.id))
        if client_time > 0:
            link = x3.link(str(message.chat.id))
            flag = "🟢 Ключ активен"
        keyboard = create_inline_keyboard([
              ("💳 Купить", "buy"),
              ("📝 Как подключить", "instruction"),
              ("🤝 Пригласи друга", "ref"),
              ("ℹ️ О нас", "About_us"),
              ("💬 Поддержка", "support")
        ])
        text = f""" 🧑‍💻 <b>Личный кабинет</b>

📆 Дней до конца подписки:  <b>{client_time}</b>

{flag}

🔑 Ключ:
<b><code>{link}</code></b>
"""
    
        bot.send_message(message.chat.id, text=text, reply_markup=keyboard, parse_mode="HTML")





@bot.callback_query_handler(func=lambda call: call.data == "next")
def next(call):
    keyboard = create_inline_keyboard([
        ("Согласен", "next2")
        ])

    bot.send_message(call.message.chat.id, text=answer.next1(), reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data == "next2")
def next2(call):
    keyboard = create_inline_keyboard([
        ("👤В личный кабинет", "menu")
        ])
    bot.send_message(call.message.chat.id, text=answer.next2(), reply_markup=keyboard, parse_mode="HTML")



@bot.callback_query_handler(func=lambda call: call.data == "menu")
def menu(call):
    if int(slon.get_row(call.message.chat.id)[5]) == 0:
        bot.send_message(call.message.chat.id, text=answer.next3(), parse_mode="HTML")
        slon.update_cell(call.message.chat.id, 5, 1)
    
    link = "..."
    flag = "🔴 Ключ неактивен"
    client_time = x3.get_time(str(call.message.chat.id))
    if client_time > 0:
        link = x3.link(str(call.message.chat.id))
        flag = "🟢 Ключ активен"
    keyboard = create_inline_keyboard([
          ("💳 Купить", "buy"),
          ("📝 Как подключить", "instruction"),
          ("🤝 Пригласи друга", "ref"),
          ("ℹ️ О нас", "About_us"),
          ("💬 Поддержка", "support")
    ])
    

    text = f""" 🧑‍💻 <b>Личный кабинет</b>

📆 Дней до конца подписки:  <b>{client_time}</b>

{flag}

🔑 Ключ:
<b><code>{link}</code></b>
"""
    
    bot.send_message(call.message.chat.id, text=text, reply_markup=keyboard, parse_mode="HTML")








@bot.callback_query_handler(func=lambda call: call.data == "ref")
def ref(call):
    bot_username = os.getenv("URL")
    link = f"https://t.me/{bot_username}?start={call.message.chat.id}"

    # Отправляем ссылку как текст (чтобы её не сокращало)
    bot.send_message(call.message.chat.id, link)

    # Кнопка "Назад"
    keyboard = create_inline_keyboard([
        ("⬅️ Назад", "menu")
    ])

    bot.send_message(call.message.chat.id, text=answer.friend_link(), reply_markup=keyboard, parse_mode="HTML")




@bot.callback_query_handler(func=lambda call: call.data == "support")
def support(call):
   keyboard = create_inline_keyboard([
      ("⬅️ Назад", "menu")
   ])
   bot.send_message(chat_id=call.message.chat.id,
                          text=answer.support(), 
                          reply_markup=keyboard,
                          parse_mode="HTML")



@bot.message_handler(commands=["support"])
def support(message):
   keyboard = create_inline_keyboard([
      ("⬅️ Назад", "menu")
   ])
   bot.send_message(chat_id=message.chat.id,
                          text=answer.support(), 
                          reply_markup=keyboard,
                          parse_mode="HTML")















@bot.callback_query_handler(func=lambda call: call.data == "instruction")
def instruction(call):
    keyboard = InlineKeyboardMarkup()
    buttons = [
        ("iPhone & iPad", "https://telegra.ph/Vless---iPhoneiPad-03-04-2"),
        ("Android", "https://telegra.ph/Vless---Android-03-04"),
        ("macOS", "https://telegra.ph/Vless---iPhoneiPad-03-04"),
        ("Windows", "https://telegra.ph/Vless---Windows-03-05")
    ]
    rows = [
        buttons[:2],  
        buttons[2:4],  
        buttons[4:6],  
    ]
    for row in rows:
        keyboard.add(*[InlineKeyboardButton(text, url=url) for text, url in row])
    keyboard.add(InlineKeyboardButton("⬅️ Назад", callback_data="menu"))
    bot.send_message(call.message.chat.id, "Выберите платформу:", reply_markup=keyboard)






@bot.callback_query_handler(func=lambda call: call.data == "About_us")
def About_us(call):
    keyboard = create_inline_keyboard([
       ("⬅️ Назад", "menu")
    ])
    bot.send_message(chat_id=call.message.chat.id, 
                          text=answer.About_us(),
                          reply_markup=keyboard,
                          parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "buy")
def buy(call):
    chat_id = call.message.chat.id
    # Отправка нового сообщения
    if int(slon.get_row(chat_id)[5]) == 1:
        bot.send_message(chat_id, text=answer.buy(), parse_mode="HTML")
        slon.update_cell(chat_id, 5, 2)

    keyboard = create_inline_keyboard([
        ("⭐1 мес - 100 звезд", "1stars"),
        ("⭐2 мес - 190 звезд", "2stars"),
        ("⭐3 мес - 280 звезд", "3stars"),
        ("⭐6 мес - 550 звезд", "6stars")
    ])
    
    bot.send_message(chat_id=chat_id, 
                     text=answer.about_price(),
                     reply_markup=keyboard)

    keyboard_2 = create_inline_keyboard([
        ("⬅️ Назад", "menu")
    ])
    
    bot.send_message(chat_id=chat_id, 
                     text=answer.stars_market(),
                     reply_markup=keyboard_2,
                     parse_mode="HTML")
    





@bot.message_handler(commands=["buy"])
def buy(message):
    chat_id = message.chat.id
    # Отправка нового сообщения
    if int(slon.get_row(chat_id)[5]) == 1:
        bot.send_message(chat_id, text=answer.buy(), parse_mode="HTML")
        slon.update_cell(chat_id, 5, 2)

    keyboard = create_inline_keyboard([
        ("⭐1 мес - 100 звезд", "1stars"),
        ("⭐2 мес - 190 звезд", "2stars"),
        ("⭐3 мес - 280 звезд", "3stars"),
        ("⭐6 мес - 550 звезд", "6stars")
    ])
    
    bot.send_message(chat_id=chat_id, 
                     text=answer.about_price(),
                     reply_markup=keyboard)

    keyboard_2 = create_inline_keyboard([
        ("⬅️ Назад", "menu")
    ])
    
    bot.send_message(chat_id=chat_id, 
                     text=answer.stars_market(),
                     reply_markup=keyboard_2,
                     parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data in {"1stars", "2stars", "3stars", "6stars"})
def invoice(call):
    
   chat_id = call.message.chat.id
   prices = {
      "1stars": [100, "1 месяц", ],
      "2stars": [190, "2 месяца"],
      "3stars": [280, "3 месяца"],
      "6stars": [550, "6 месяцев"]
   }
   item = prices.get(call.data)  
   bot.send_invoice(
      chat_id=chat_id,
      title=item[1],
      description="Приобрести " + item[1],
      provider_token="",
      currency="XTR",
      prices= [LabeledPrice(label="subscription", amount=item[0])],
      start_parameter="premium_subscription",
      invoice_payload=str(item[1])
   )



@bot.pre_checkout_query_handler(func=lambda query: True)
def precheckout_handler(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)



@bot.message_handler(content_types=['successful_payment'])
def successful_payment(message):
    invoice_payload = message.successful_payment.invoice_payload
    keyboard = create_inline_keyboard([
      ("👤В личный кабинет", "menu")
   ])
    ref_id = int(slon.get_row(message.chat.id)[4])
    match invoice_payload:
        case "1 месяц":
            if ref_id != 0:
                bot.send_message(ref_id, text = answer.ref_info())
                slon.update_cell(message.chat.id, 4, 0)
                x3.update_client(20, str(ref_id))
            x3.update_client(30, str(message.chat.id))
        case "2 месяца":
            if ref_id != 0:
                bot.send_message(ref_id, text = answer.ref_info())
                slon.update_cell(message.chat.id, 4, 0)
                x3.update_client(20, str(ref_id))
            x3.update_client(60, str(message.chat.id))
        case "3 месяца":
            if ref_id != 0:
                bot.send_message(ref_id, text = answer.ref_info())
                slon.update_cell(message.chat.id, 4, 0)
                x3.update_client(20, str(ref_id))
            x3.update_client(90, str(message.chat.id))
        case "6 месяцев":
            if ref_id != 0:
                bot.send_message(ref_id, text = answer.ref_info())
                slon.update_cell(message.chat.id, 4, 0)
                x3.update_client(20, str(ref_id))
            x3.update_client(180, str(message.chat.id))
    bot.send_message(message.chat.id, f"Вы приобрели {invoice_payload}", reply_markup=keyboard)


updates = bot.get_updates()
if updates:
    for update in updates:
        bot.process_new_updates([update])



while True:
    try:
        bot.polling(none_stop=True, timeout=60)
    except Exception as e:
        print(f"Ошибка polling: {e}")
        time.sleep(5)  # Подождать 5 секунд и запустить снова
