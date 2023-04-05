from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler, ConversationHandler
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from callopenai import *
from hiking import *
from tvshow import *
from cookvideo import *
import os
import logging
import redis
import json
import datetime


global redis1

userSelectedTexts = [
    "select the desired route",
    "select the desired tv show",
    "select the desired cooking videos",
    "select read or write tv show review",
    "Please input your tv show review here"
]

SLECTTVSHOW = range(1)

def main():
    updater = Updater(token=(os.environ['ACCESS_TOKEN']), use_context=True)
    dispatcher = updater.dispatcher
    global redis1
    redis1 = redis.Redis(host=(os.environ['HOST']), 
                         password=(os.environ['REDIS_PASSWORD']), 
                         port=(os.environ['REDISPORT']))
    # You can set this logging module, so you will know when and why things do not work as expected
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    tvshow_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("tvshow", tvshow)],
        states={
            SLECTTVSHOW: [MessageHandler(Filters.text, writeReview)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # register a dispatcher to handle message: here we register an echo dispatcher
    default_handler = MessageHandler(Filters.text & (~Filters.command), welcome)
    # on different commands - answer in Telegram
    dispatcher.add_handler(tvshow_conv_handler)
    # dispatcher.add_handler(CommandHandler("add", writeReview))
    dispatcher.add_handler(CommandHandler("hello", hello))
    dispatcher.add_handler(CommandHandler("callai", callai))
    dispatcher.add_handler(CommandHandler("hiking", hiking))
    # dispatcher.add_handler(CommandHandler("tvshow", tvshow))
    dispatcher.add_handler(CommandHandler("cook", cook))
    dispatcher.add_handler(CallbackQueryHandler(userselected))
    dispatcher.add_handler(MessageHandler(Filters.command, welcome))
    dispatcher.add_handler(default_handler)
    dispatcher.add_error_handler(error_handler)

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

def cancel(update: Update, context):
    return ConversationHandler.END


def writeReview(update: Update, context: CallbackContext)-> None:
    try:
        global readwrite
        if readwrite=="Write":
            msg = update.message.text
            global selectedLink
            tvReview = get_tv_review(selectedLink)
            review = {"link" : tvReview["link"], "title" : tvReview["title"], "time" : datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "content":msg}
            review_json = json.dumps(review)
            redis1.lpush(update.message.from_user.id, review_json)
            context.bot.send_message(chat_id=update.effective_chat.id, text= "Thank you for your review!")
        welcome(update, context)
        return ConversationHandler.END
        
    except (IndexError, ValueError):
        update.message.reply_text('Error Occur')

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
                text="Give me other tv shows", callback_data=0)])
    reply_keyboard_markup = InlineKeyboardMarkup(btnOptions)
    context.bot.send_message(chat_id=update.effective_chat.id, text=userSelectedTexts[1], reply_markup=reply_keyboard_markup)
    # context.bot.send_message(chat_id=update.effective_chat.id, text=userSelectedTexts[1])
    return SLECTTVSHOW
    

def cook(update: Update, context: CallbackContext) -> None:
    global randomCookVideos
    randomCookVideos = get_cooking_video_information()
    # print(randomShows)
    btnOptions = []
    for index, cookVideo in enumerate(randomCookVideos):
        btnOptions.append([InlineKeyboardButton(
                text=cookVideo['title'], callback_data=index)])
        #  url=cookVideo['link']
    btnOptions.append( [InlineKeyboardButton(
                text="Give me other cooking videos", callback_data=len(randomCookVideos))])
    reply_keyboard_markup = InlineKeyboardMarkup(btnOptions)
    context.bot.send_message(chat_id=update.effective_chat.id, text=userSelectedTexts[2], reply_markup=reply_keyboard_markup)


def userselected(update: Update, context: CallbackContext) -> None:
    global randomPhotos
    global randomCookVideos
    # print(update.callback_query)
    callback_data = update.callback_query.data
    callback_text = update.callback_query.message.text
    if callback_text == userSelectedTexts[0]:
        selectedIndex = int(callback_data)
        if selectedIndex < len(randomPhotos):
            selectedText = update.callback_query.message.reply_markup.inline_keyboard[selectedIndex][0].text
            context.bot.send_photo(chat_id=update.effective_chat.id, photo=randomPhotos[selectedIndex])
            context.bot.send_message(chat_id=update.effective_chat.id, text='''Here is the photo from {}'''.format(selectedText))
            context.bot.send_message(chat_id=update.effective_chat.id, text='Click /start to try again')
        else:
            hiking(update, context)
    elif callback_text == userSelectedTexts[1]:
        global selectedLink
        selectedLink = callback_data
        if selectedLink.isnumeric():
            tvshow(update, context)
        else:
            tvReview = get_tv_review(selectedLink)
            context.bot.send_photo(chat_id=update.effective_chat.id, photo=tvReview['image'])
            context.bot.send_message(chat_id=update.effective_chat.id, 
                                     text=userSelectedTexts[3], reply_markup=get_read_write_option())
    elif callback_text == userSelectedTexts[2]:
        selectedIndex = int(callback_data)
        if selectedIndex < len(randomCookVideos):
            selectedVideo = randomCookVideos[selectedIndex]
            context.bot.send_message(chat_id=update.effective_chat.id, 
                                     parse_mode='HTML',
                                     text=selectedVideo['link'])
            welcome(update, context)
        else:
            cook(update, context)
    elif callback_text == userSelectedTexts[3]:
        tvReview = get_tv_review(selectedLink)
        global readwrite
        if callback_data == "Read":
            readwrite = "Read"
            context.bot.send_message(chat_id=update.effective_chat.id, text=tvReview['review'])
            context.bot.send_message(chat_id=update.effective_chat.id, text='Click /start to try again')
        else:
            readwrite = "Write"
            context.bot.send_message(chat_id=update.effective_chat.id, text=userSelectedTexts[4])

def error_handler(update, context):
    """Log the error and send a message to the user."""
    logging.warning('Update "%s" caused error "%s"', update, context.error)
    context.bot.send_message(chat_id=update.message.chat_id, text="Sorry, an error occurred.")


def welcome(update, context):
    welcome_message = '''Hello and welcome, {}.
I'm your leisure activity chatbot assistant and provide you 3 functions.
send /hiking to check hiking information in Hong Kong
send /tvshow to read or write review to TV show in Neflex
send /cook to view the cooking video from youtube'''.format(
        update.message.from_user.first_name)
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=welcome_message)


def get_read_write_option():
    reply_keyboard_markup = InlineKeyboardMarkup(
        [
            [
            InlineKeyboardButton(
                text="Read", callback_data="Read"),
            InlineKeyboardButton(
                text="Write", callback_data="Write")
            ]
        ]
    )
    return reply_keyboard_markup


if __name__ == '__main__':
    main()


