import logging
import sqlite3
import os
import secrets
import string
import datetime
import pytz
import time
from telegram import InlineQueryResultArticle, InputTextMessageContent, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, InlineQueryHandler, CallbackQueryHandler, ChosenInlineResultHandler, CallbackContext

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

spam_cache = {}
consecutive_setups = {}

def init_db():
    with sqlite3.connect('users.db') as conn:
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS user_prefs (user_id INTEGER PRIMARY KEY, lang_code TEXT)')

def get_user_lang(user_id):
    with sqlite3.connect('users.db') as conn:
        c = conn.cursor()
        c.execute("SELECT lang_code FROM user_prefs WHERE user_id == ?", (user_id,))
        result = c.fetchone()
        return result[0] if result else None

def set_user_lang(user_id, lang_code):
    with sqlite3.connect('users.db') as conn:
        c = conn.cursor()
        c.execute("REPLACE INTO user_prefs (user_id, lang_code) VALUES (?, ?)", (user_id, lang_code))

def generate_random_id():
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(50))

def format_az_date(current_time, month_name):
    minute = current_time.minute
    ending = "-da" if minute in [0, 6, 9, 10, 16, 19, 26, 29, 30, 36, 39, 40, 46, 49, 56, 59] else "-də"
    return f"{current_time.day} {month_name} saat {current_time.hour:02d}:{minute:02d}{ending}"

def format_ua_date(current_time, month_name):
    hour = current_time.hour
    preposition = "об" if hour == 11 else "о"
    return f"{current_time.day} {month_name} {preposition} {hour:02d}:{current_time.minute:02d}"

LANGUAGES = {
    "az": {
        "tz": "Asia/Baku",
        "months": {
            1: "yanvar", 2: "fevral", 3: "mart", 4: "aprel", 5: "may", 6: "iyun",
            7: "iyul", 8: "avqust", 9: "sentyabr", 10: "oktyabr", 11: "noyabr", 12: "dekabr"
        },
        "date_formatter": format_az_date,
        "message_format": "Yazıb bildirmək istəyirəm ki, {date} {item} ilə heç bir əlaqəm yoxdur.",
        "ui": {
            "setup_title": "🌐 Dil seçimi",
            "setup_desc": "Dili dəyişmək üçün toxunun",
            "setup_msg": "Dil seçin:",
            "limit_title": "🚫 Limit",
            "spam_msg": "Bəlkə biraz yavaşlayaq?",
            "success_msg": "Dil seçildi. İzahat yazmaq üçün, botu yenidən çağırın.",
            "success_edit": "🇦🇿 Azərbaycanca",
            "unauthorized_click": "Bir dəqiqə xətdə qal"
        },
        "items": [
            {'title': '🖼️ Şəkil izahatı', 'desc': 'Gördüyüm şəkilə görə izahat', 'text': 'gördüyüm şəkil', 'thumb': 'https://raw.githubusercontent.com/Iniretur/izahat-bot/refs/heads/master/assets/image_az.png'},
            {'title': '🎞️ Video izahatı', 'desc': 'Gördüyüm videoya görə izahat', 'text': 'gördüyüm video', 'thumb': 'https://raw.githubusercontent.com/Iniretur/izahat-bot/refs/heads/master/assets/video_az.png'},
            {'title': '👂 Səs izahatı', 'desc': 'Eşitdiyim səsə görə izahat', 'text': 'eşitdiyim səs', 'thumb': 'https://raw.githubusercontent.com/Iniretur/izahat-bot/refs/heads/master/assets/sound_az.png'},
            {'title': '📃 Mətn izahatı', 'desc': 'Oxuduğum mətnə görə izahat', 'text': 'oxuduğum mətn', 'thumb': 'https://raw.githubusercontent.com/Iniretur/izahat-bot/refs/heads/master/assets/text_az.png'},
            {'title': '🫁 Oksigen izahatı', 'desc': 'Nəfəs aldığım havaya görə izahat', 'text': 'nəfəs aldığım hava', 'thumb': 'https://raw.githubusercontent.com/Iniretur/izahat-bot/refs/heads/master/assets/air_az.png'}
        ]
    },
    "ua": {
        "tz": "Europe/Kyiv",
        "months": {
            1: "січня", 2: "лютого", 3: "березня", 4: "квітня", 5: "травня", 6: "червня",
            7: "липня", 8: "серпня", 9: "вересня", 10: "жовтня", 11: "листопада", 12: "грудня"
        },
        "date_formatter": format_ua_date,
        "message_format": "Хочу повідомити, що не маю жодного відношення до {item} {date}.",
        "ui": {
            "setup_title": "🌐 Вибір мови",
            "setup_desc": "Натисніть тут, щоб змінити мову",
            "setup_msg": "Оберіть мову:",
            "limit_title": "🚫 Ліміт",
            "spam_msg": "Пiшов нахуй",
            "success_msg": "Мову обрано. Щоб написати пояснювальну, викличте бота знову.",
            "success_edit": "🇺🇦 Українська",
            "unauthorized_click": "Пiшов нахуй, це не твоє"
        },
        "items": [
            {'title': '🖼️ Пояснювальна за фото', 'desc': 'Пояснення щодо побаченого фото', 'text': 'побаченого фото', 'thumb': 'https://raw.githubusercontent.com/Iniretur/izahat-bot/refs/heads/master/assets/image_ua.png'},
            {'title': '🎞️ Пояснювальна за відео', 'desc': 'Пояснення щодо побаченого відео', 'text': 'побаченого відео', 'thumb': 'https://raw.githubusercontent.com/Iniretur/izahat-bot/refs/heads/master/assets/video_ua.png'},
            {'title': '👂 Пояснювальна за аудіо', 'desc': 'Пояснення щодо почутого звуку', 'text': 'почутого звуку', 'thumb': 'https://raw.githubusercontent.com/Iniretur/izahat-bot/refs/heads/master/assets/sound_ua.png'},
            {'title': '📃 Пояснювальна за текст', 'desc': 'Пояснення щодо прочитаного тексту', 'text': 'прочитаного тексту', 'thumb': 'https://raw.githubusercontent.com/Iniretur/izahat-bot/refs/heads/master/assets/text_ua.png'},
            {'title': '🫁 Пояснювальна за повітря', 'desc': 'Пояснення щодо повітря, яким дихаю', 'text': 'повітря, яким дихаю', 'thumb': 'https://raw.githubusercontent.com/Iniretur/izahat-bot/refs/heads/master/assets/air_ua.png'}
        ]
    },
    "en": {
        "ui": {
            "setup_title": "🌐 Select language",
            "setup_desc": "Tap here to select your language",
            "setup_msg": "Choose your language:",
            "limit_title": "🚫 Limit",
            "spam_msg": "Do not spam! Please wait.",
            "success_msg": "Language selected. Call the bot again.",
            "success_edit": "✅ Selected",
            "unauthorized_click": "This button is not for you!"
        }
    }
}

def clean_caches():
    current_time = time.time()
    stale_users = [uid for uid, ts in spam_cache.items() if current_time - ts > 300]
    for uid in stale_users:
        del spam_cache[uid]
        if uid in consecutive_setups:
            del consecutive_setups[uid]

def get_formatted_message(lang_code, item_text):
    lang = LANGUAGES[lang_code]
    tz = pytz.timezone(lang["tz"])
    current_time = datetime.datetime.now(tz)
    month_name = lang["months"].get(current_time.month, "")
    formatted_date = lang["date_formatter"](current_time, month_name)
    return lang["message_format"].format(date=formatted_date, item=item_text)

def inline_command(update: Update, context: CallbackContext) -> None:
    clean_caches()
    
    user_id = update.inline_query.from_user.id
    lang_code = get_user_lang(user_id)
    results = []

    setups_count = consecutive_setups.get(user_id, 0)
    
    ui_lang = lang_code if lang_code else "en"
    ui = LANGUAGES[ui_lang]["ui"]

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🇦🇿 Azərbaycanca", callback_data=f"setlang_az_{user_id}")],
        [InlineKeyboardButton("🇺🇦 Українська", callback_data=f"setlang_ua_{user_id}")]
    ])

    if setups_count >= 3:
        setup_article = InlineQueryResultArticle(
            id=generate_random_id() + "_spam",
            title=ui["limit_title"],
            description=ui["spam_msg"],
            thumb_url="https://raw.githubusercontent.com/Iniretur/izahat-bot/refs/heads/master/assets/lang_spam.png",
            input_message_content=InputTextMessageContent(ui["spam_msg"])
        )
    else:
        setup_article = InlineQueryResultArticle(
            id=generate_random_id() + "_setup",
            title=ui["setup_title"],
            description=ui["setup_desc"],
            thumb_url="https://raw.githubusercontent.com/Iniretur/izahat-bot/refs/heads/master/assets/lang.png",
            input_message_content=InputTextMessageContent(ui["setup_msg"]),
            reply_markup=keyboard
        )

    if lang_code == None:
        results.append(setup_article)
    else:
        lang_data = LANGUAGES[lang_code]
        for item in lang_data["items"]:
            msg_content = get_formatted_message(lang_code, item["text"])
            results.append(
                InlineQueryResultArticle(
                    id=generate_random_id() + "_item",
                    title=item["title"],
                    description=item["desc"],
                    thumb_url=item["thumb"],
                    input_message_content=InputTextMessageContent(msg_content)
                )
            )
        results.append(setup_article)

    update.inline_query.answer(results, cache_time=0)

def chosen_result_handler(update: Update, context: CallbackContext) -> None:
    result = update.chosen_inline_result
    user_id = result.from_user.id
    
    if result.result_id.endswith("_setup"):
        consecutive_setups[user_id] = consecutive_setups.get(user_id, 0) + 1
        spam_cache[user_id] = time.time()
    elif result.result_id.endswith("_item"):
        consecutive_setups[user_id] = 0

def callback_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data

    if data.startswith("setlang_"):
        parts = data.split("_")
        lang = parts[1]
        target_user = int(parts[2])

        clicker_id = query.from_user.id
        clicker_lang = get_user_lang(clicker_id)
        clicker_ui_lang = clicker_lang if clicker_lang else "en"

        if clicker_id == target_user:
            current_time = time.time()
            last_click = spam_cache.get(target_user, 0)
            spam_lang = current_lang if (current_lang := get_user_lang(target_user)) else "en"

            if current_time - last_click < 3:
                query.answer(LANGUAGES[spam_lang]["ui"]["spam_msg"], show_alert=True)
                return
            
            spam_cache[target_user] = current_time

            set_user_lang(target_user, lang)

            ui = LANGUAGES[lang]["ui"]

            try:
                context.bot.edit_message_text(
                    text=ui["success_edit"],
                    inline_message_id=query.inline_message_id
                )
            except Exception:
                pass

            query.answer(ui["success_msg"], show_alert=True)
        else:
            unauthorized_msg = LANGUAGES[clicker_ui_lang]["ui"]["unauthorized_click"]
            query.answer(unauthorized_msg, show_alert=True)

def main() -> None:
    init_db()
    updater = Updater(os.environ['TOKEN'])
    dispatcher = updater.dispatcher

    dispatcher.add_handler(InlineQueryHandler(inline_command))
    dispatcher.add_handler(ChosenInlineResultHandler(chosen_result_handler))
    dispatcher.add_handler(CallbackQueryHandler(callback_handler))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()