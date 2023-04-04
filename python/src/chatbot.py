from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from callopenai import *
from hiking import *
from tvshow import *
import os
import logging
import redis

global redis1

userSelectedTexts = [
    "select the desired route",
    "select the desired tv show"
]

def main():
    updater = Updater(token=(os.environ['ACCESS_TOKEN']), use_context=True)
    dispatcher = updater.dispatcher
    global redis1
    redis1 = redis.Redis(host=(os.environ['HOST']), 
                         password=(os.environ['REDIS_PASSWORD']), 
                         port=(os.environ['REDISPORT']))
    # You can set this logging module, so you will know when and why things do not work as expected
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    # register a dispatcher to handle message: here we register an echo dispatcher
    echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
    dispatcher.add_handler(echo_handler)
    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("add", add))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("hello", hello))
    dispatcher.add_handler(CommandHandler("callai", callai))
    dispatcher.add_handler(CommandHandler("hiking", hiking))
    dispatcher.add_handler(CommandHandler("tvshow", tvshow))
    dispatcher.add_handler(CallbackQueryHandler(userselected))
    dispatcher.add_handler(MessageHandler(Filters.command, help_command))
    # dispatcher.add_error_handler(error_handler)

    # To start the bot:
    updater.start_polling()
    updater.idle()

def echo(update, context):
    reply_message = update.message.text.upper()
    logging.info("Update: " + str(update))
    logging.info("context: " + str(context))
    context.bot.send_message(chat_id=update.effective_chat.id, text= reply_message)

    # Define a few command handlers. These usually take the two arguments update and
    # context. Error handlers also receive the raised TelegramError object in error.

def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Helping you helping you. lab6')

def hello(update: Update, context: CallbackContext) -> None:
    msg = context.args[0]
    update.message.reply_text(f'Good day, {msg}!')

def add(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /add is issued."""
    try:
        global redis1
        logging.info(context.args[0])
        msg = context.args[0] # /add keyword <-- this should store the keyword
        redis1.incr(msg)
        update.message.reply_text('You have said ' + msg + ' for ' +
        redis1.get(msg).decode('UTF-8') + ' times.')
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /add <keyword>')

def callai(update: Update, context: CallbackContext) -> None:
    msg = " ".join(context.args)
    response = checkOpenAI(msg)
    update.message.reply_text(response)

def hiking(update: Update, context: CallbackContext) -> None:
    global randomPhotos
    hiking_information = get_hiking_information()
    btnOptions = []
    for index, locDesc in enumerate(hiking_information[0]):
        btnOptions.append( [InlineKeyboardButton(
                text=", ".join(locDesc), callback_data=index)])
    btnOptions.append( [InlineKeyboardButton(
                text="Give me other route", callback_data=len(hiking_information[0]))])
    reply_keyboard_markup = InlineKeyboardMarkup(btnOptions)
    randomPhotos = hiking_information[1]
    # context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo)
    context.bot.send_message(chat_id=update.effective_chat.id, text=userSelectedTexts[0], reply_markup=reply_keyboard_markup)

def tvshow(update: Update, context: CallbackContext) -> None:
    global randomShows
    randomShows = get_tv_information()
    # print(randomShows)
    btnOptions = []
    for show in randomShows:
        btnOptions.append( [InlineKeyboardButton(
                text=show['title'], callback_data=show['link'])])
    btnOptions.append( [InlineKeyboardButton(
                text="Give me other tv shows", callback_data=len(randomShows[1]))])
    reply_keyboard_markup = InlineKeyboardMarkup(btnOptions)
    context.bot.send_message(chat_id=update.effective_chat.id, text=userSelectedTexts[1], reply_markup=reply_keyboard_markup)


def userselected(update: Update, context: CallbackContext) -> None:
    global randomPhotos
    # print(update.callback_query)
    callback_data = update.callback_query.data
    callback_text = update.callback_query.message.text
    if callback_text == userSelectedTexts[0]:
        selectedIndex = int(callback_data)
        if selectedIndex < len(randomPhotos):
            selectedText = update.callback_query.message.reply_markup.inline_keyboard[selectedIndex][0].text
            context.bot.send_photo(chat_id=update.effective_chat.id, photo=randomPhotos[selectedIndex])
            context.bot.send_message(chat_id=update.effective_chat.id, text='''Please find the photo of {}'''.format(selectedText))
        else:
            hiking(update, context)
    elif callback_text == userSelectedTexts[1]:
        selectedLink = callback_data
        print(selectedLink)
        tvshow(update, context)

def error_handler(update, context):
    """Log the error and send a message to the user."""
    logging.warning('Update "%s" caused error "%s"', update, context.error)
    context.bot.send_message(chat_id=update.message.chat_id, text="Sorry, an error occurred.")


def welcome(update, context):
    welcome_message = '''hello, {}! Welcome to chatbot.
We have provided three features for you.
You can send /cookshare to share cooking video to us!
Or you can send /sharemovie to share cooking video to us!
Or you can select hiking to exploer hiking route from us! '''.format(
        update.message.from_user.first_name)
    
    reply_keyboard_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="Hiking", callback_data="2")]
    ])
    user = update.message.from_user
    print('You talk with user {} and his user ID: {} '.format(
        user['username'], user['id']))
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=welcome_message, reply_markup=reply_keyboard_markup)

if __name__ == '__main__':
    main()