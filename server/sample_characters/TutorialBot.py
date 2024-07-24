import logging
import os
from dotenv import load_dotenv, find_dotenv
from datetime import datetime, timedelta, timezone
import pytz

from telegram import Update, ForceReply, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler

load_dotenv(find_dotenv())
ist = timezone(timedelta(hours=5, minutes=30))

tg_api_key = os.getenv("TELEGRAM_API_KEY_SAJNI123")


logger = logging.getLogger(__name__)

# Store bot screaming status
screaming = False

# Pre-assign menu text
FIRST_MENU = "<b>Menu 1</b>\n\nA beautiful menu with a shiny inline button."
SECOND_MENU = "<b>Menu 2</b>\n\nA better menu with even more shiny inline buttons."

# Pre-assign button text
NEXT_BUTTON = "Next"
BACK_BUTTON = "Back"
TUTORIAL_BUTTON = "Tutorial"

# Build keyboards
FIRST_MENU_MARKUP = InlineKeyboardMarkup([[
    InlineKeyboardButton(NEXT_BUTTON, callback_data=NEXT_BUTTON)
]])
SECOND_MENU_MARKUP = InlineKeyboardMarkup([
    [InlineKeyboardButton(BACK_BUTTON, callback_data=BACK_BUTTON)],
    [InlineKeyboardButton(TUTORIAL_BUTTON, url="https://core.telegram.org/bots/api")]
])

def echo(update: Update, context: CallbackContext) -> None:
    """
    This function would be added to the dispatcher as a handler for messages coming from the Bot API
    """

    # Print to console
    print(f'{update.message.from_user.first_name} wrote {update.message.text}')
    print(f'TutorialBot >> echo > update:{update},context:{context}\n\n')
    query_timestamp = update.message.date
    # query_timestamp = pytz.timezone("Asia/Kolkata").localize(query_timestamp)
    user_first_name = update.message.from_user.first_name
    user_is_bot = update.message.from_user.is_bot
    v_user_name = update.message.from_user.username
    user_tg_id = update.message.from_user.id
    user_language_code = update.message.from_user.language_code
    print(f"*********** query_timestamp:{query_timestamp}, user_first_name:{user_first_name}, user_is_bot:{user_is_bot}, v_user_name:{v_user_name}, user_tg_id:{user_tg_id}, user_language_code:{user_language_code}\n\n")

    if screaming and update.message.text:
        print("**** Log 1")
        context.bot.send_message(
            update.message.chat_id,
            update.message.text.upper(),
            # To preserve the markdown, we attach entities (bold, italic...)
            entities=update.message.entities
        )
    else:
        print("**** Log 2: update.message.chat_id",update.message.chat_id)
        # This is equivalent to forwarding, without the sender's name
        update.message.copy(update.message.chat_id)


def scream(update: Update, context: CallbackContext) -> None:
    """
    This function handles the /scream command
    """
    print(f"TutorialBot >> scream > update:{update},context:{context}")

    global screaming
    screaming = True


def whisper(update: Update, context: CallbackContext) -> None:
    """
    This function handles /whisper command
    """
    print(f"TutorialBot >> whisper > update:{update},context:{context}")

    global screaming
    screaming = False


def menu(update: Update, context: CallbackContext) -> None:
    """
    This handler sends a menu with the inline buttons we pre-assigned above
    """
    print(f"TutorialBot >> menu > update:{update},context:{context}")

    context.bot.send_message(
        update.message.from_user.id,
        FIRST_MENU,
        parse_mode=ParseMode.HTML,
        reply_markup=FIRST_MENU_MARKUP
    )


def button_tap(update: Update, context: CallbackContext) -> None:
    """
    This handler processes the inline buttons on the menu
    """
    print(f"TutorialBot >> button_tap > update:{update},context:{context}")
    data = update.callback_query.data
    text = ''
    markup = None

    if data == NEXT_BUTTON:
        text = SECOND_MENU
        markup = SECOND_MENU_MARKUP
    elif data == BACK_BUTTON:
        text = FIRST_MENU
        markup = FIRST_MENU_MARKUP

    # Close the query to end the client-side loading animation
    update.callback_query.answer()

    # Update message content with corresponding menu section
    update.callback_query.message.edit_text(
        text,
        ParseMode.HTML,
        reply_markup=markup
    )


def main() -> None:
    updater = Updater(tg_api_key)

    # Get the dispatcher to register handlers
    # Then, we register each handler and the conditions the update must meet to trigger it
    dispatcher = updater.dispatcher

    # Register commands
    dispatcher.add_handler(CommandHandler("scream", scream))
    dispatcher.add_handler(CommandHandler("whisper", whisper))
    dispatcher.add_handler(CommandHandler("menu", menu))

    # Register handler for inline buttons
    dispatcher.add_handler(CallbackQueryHandler(button_tap))

    # Echo any message that is not a command
    dispatcher.add_handler(MessageHandler(~Filters.command, echo))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()


if __name__ == '__main__':
    main()