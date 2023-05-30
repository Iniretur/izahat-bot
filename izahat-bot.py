import logging
from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import Updater, InlineQueryHandler, CallbackContext
import datetime
import secrets
import string
import os

# Mapping of month names in Azerbaijani
MONTH_NAMES = {
    1: "yanvar",
    2: "fevral",
    3: "mart",
    4: "aprel",
    5: "may",
    6: "iyun",
    7: "iyul",
    8: "avqust",
    9: "sentyabr",
    10: "oktyabr",
    11: "noyabr",
    12: "dekabr"
}

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_random_id():
    # Define the characters to choose from
    characters = string.ascii_letters + string.digits

    # Generate a random string of the specified length
    random_string = ''.join(secrets.choice(characters) for _ in range(64))
    return random_string

def get_current_date() -> str:
    # Get the current local time
    current_time = datetime.datetime.now()

    # Get the day, month, hour, and minute components
    day = current_time.day
    month = current_time.month
    hour = current_time.hour + 4
    minute = current_time.minute

    # Format the month name in Azerbaijani
    month_name = MONTH_NAMES.get(month, "")

    # Format the time as "DD MMMM saat HH:MM"
    formatted_date = f"{day} {month_name} saat {hour:02d}:{minute:02d}"

    # Determine the appropriate ending for minutes
    if minute in [0, 6, 9, 10, 16, 19, 26, 29, 30, 36, 39, 40, 46, 49, 56, 59]:
        ending = "-da"
    else:
        ending = "-də"

    # Add the ending to the formatted datetime
    message = formatted_date + ending

    return message

def generate_message_head() -> str:
    message = "Yazıb bildirmək istəyirəm ki, "
    return message

def generate_message_tail() -> str:
    message = " ilə heç bir əlaqəm yoxdur."
    return message

# Inline command handler
def inline_command(update: Update, context: CallbackContext) -> None:
    query = update.inline_query.query

    results = [
            InlineQueryResultArticle(
                id=generate_random_id(),
                title='Şəkil izahatı',
                description='',
                input_message_content=InputTextMessageContent(generate_message_head() + get_current_date() + " gördüyüm şəkil" + generate_message_tail())
            ),
            InlineQueryResultArticle(
                id=generate_random_id(),
                title='Video izahatı',
                description='',
                input_message_content=InputTextMessageContent(generate_message_head() + get_current_date() + " gördüyüm video" + generate_message_tail())
            ),
            InlineQueryResultArticle(
                id=generate_random_id(),
                title='Səs izahatı',
                description='',
                input_message_content=InputTextMessageContent(generate_message_head() + get_current_date() + " eşitdiyim səs" + generate_message_tail())
            ),
            InlineQueryResultArticle(
                id=generate_random_id(),
                title='Mətn izahatı',
                description='',
                input_message_content=InputTextMessageContent(generate_message_head() + get_current_date() + " oxuduğum mətn" + generate_message_tail())
            )
        ]

    update.inline_query.answer(results, cache_time=0)

# Set up the Telegram bot
def main() -> None:
    updater = Updater(os.environ['TOKEN'])
    dispatcher = updater.dispatcher

    # Add the inline command handler
    dispatcher.add_handler(InlineQueryHandler(inline_command))

    # Start the bot
    updater.start_polling()
    logger.info('Bot started')

    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()
