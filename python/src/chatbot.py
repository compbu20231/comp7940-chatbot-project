from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters, ConversationHandler
from hiking import *
from tvshow import *
from cookvideo import *
from urllib.parse import urlparse
import redis
import os
import json
import logging




redis_conn = redis.Redis(host=(os.environ['HOST']), 
                         password=(os.environ['REDIS_PASSWORD']), 
                         port=(os.environ['REDISPORT']))


HIKING_OPTIONS, HIKING_READ, HIKING_WRITE, HIKING_READ_PHOTO  = range(4)
TVSHOW_READ_PHOTO, TVSHOW_WRITE_PROMPT, TVSHOW_WRITE, TVSHOW_END  = range(4)
COOKING_OPTIONS, COOKING_READ, COOKING_WRITE, COOKING_READ_VIDEO  = range(4)

def hiking_entrance(update, context):
    read_text = "Read hiking route / photo"
    write_text = "Share hiking route / photo"
    reply_markup = get_read_write_option(read_text, write_text, str(HIKING_READ), str(HIKING_WRITE))
    update.message.reply_text("Choose an option:", reply_markup=reply_markup)
    return HIKING_OPTIONS

def cooking_entrance(update, context):
    read_text = "Read cooking video"
    write_text = "Share cooking video"
    reply_markup = get_read_write_option(read_text, write_text, str(COOKING_READ), str(COOKING_WRITE))
    update.message.reply_text("Choose an option:", reply_markup=reply_markup)
    return COOKING_OPTIONS

def hiking_read(update, context):
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
    context.bot.send_message(chat_id=update.effective_chat.id, text="Please select the hiking route", reply_markup=reply_keyboard_markup)
    return HIKING_READ_PHOTO

def cooking_read(update, context):
    global randomCookVideos
    randomCookVideos = get_cooking_video_information()
    btnOptions = []
    for index, cookVideo in enumerate(randomCookVideos):
        btnOptions.append([InlineKeyboardButton(
                text=cookVideo['title'], callback_data=index)])
    btnOptions.append( [InlineKeyboardButton(
                text="Give me other cooking videos", callback_data=len(randomCookVideos))])
    reply_keyboard_markup = InlineKeyboardMarkup(btnOptions)
    context.bot.send_message(chat_id=update.effective_chat.id, text="Please select the video", reply_markup=reply_keyboard_markup)
    return COOKING_READ_VIDEO

def tvshow_read(update, context):
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
    context.bot.send_message(chat_id=update.effective_chat.id, text="Please select the TV Show", reply_markup=reply_keyboard_markup)
    # context.bot.send_message(chat_id=update.effective_chat.id, text=userSelectedTexts[1])
    return TVSHOW_READ_PHOTO
 
def hiking_photo(update, context):
    query = update.callback_query
    global randomPhotos
    try:
        index = int(query.data)
        photo = randomPhotos[int(query.data)]
        text = update.callback_query.message.reply_markup.inline_keyboard[index][0].text
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo)
        context.bot.send_message(chat_id=update.effective_chat.id, text="Here is the photo from {}".format(text))
        context.bot.send_message(chat_id=update.effective_chat.id, text='Click /start to try again')
        return ConversationHandler.END
    except:
        return hiking_read(update, context)

def cooking_video(update, context):
    query = update.callback_query
    global randomCookVideos
    try:
        selectedVideo = randomCookVideos[int(query.data)]
        context.bot.send_message(chat_id=update.effective_chat.id, 
                                     parse_mode='HTML',
                                     text=selectedVideo['link'])
        context.bot.send_message(chat_id=update.effective_chat.id, text='Click /start to try again')
        return ConversationHandler.END
    except:
        return cooking_read(update, context)

def tvshow_photo(update, context):
    query = update.callback_query
    global randomShows
    try:
        if isinstance(query.data, int):
            tvshow_read(update, context)
        else:
            global tvReview
            tvReview = get_tv_review(query.data)
            if tvReview['image'] is not None:
                context.bot.send_photo(chat_id=update.effective_chat.id, photo=tvReview['image'])
            if tvReview['review'] != 'review not found':
                context.bot.send_message(chat_id=update.effective_chat.id, text=tvReview['review'])
                reply_markup = get_read_write_option('Yes', 'No', str(TVSHOW_WRITE), str(TVSHOW_END))
                context.bot.send_message(chat_id=update.effective_chat.id, 
                                        text='Do you want to write the review of this show ?', reply_markup=reply_markup)
                return TVSHOW_WRITE_PROMPT
            else:
                tvshow_read(update, context)
    except:
        return tvshow_read(update, context)
  

def hiking_write(update, context):
    message = update.message
    if len(message.photo) > 0 and message.caption is not None:
        photo_file = message.photo[-1].get_file()
        hiking_data = {
            "image" : photo_file.file_path,
            "id" : message.chat.id,
            "route" : message.caption
        }
        redis_conn.lpush("hiking", json.dumps(hiking_data))
        update.message.reply_text("Thank you for your share, Click /start to try again")
        return ConversationHandler.END
    else:
        update.message.reply_text("Hiking photo or caption is missing, please input again!")

def cooking_write(update, context):
    message = update.message
    if message.video is not None:
        video_id = update.message.video.file_id
        cooking_data = {
            "video_id" : video_id,
            "caption": message.caption,
            "id" : message.chat.id,
        }
        redis_conn.lpush("cooking", json.dumps(cooking_data))
        update.message.reply_text("Thank you for your share, Click /start to try again")
        return ConversationHandler.END
    elif message.text is not None:
        parsed_url = urlparse(message.text)
        if parsed_url.scheme and parsed_url.netloc:
            cooking_data = {
                "link" : message.text,
                "id" : message.chat.id,
            }
            redis_conn.lpush("cooking", json.dumps(cooking_data))
            update.message.reply_text("Thank you for your share, Click /start to try again")
            return ConversationHandler.END
        else:
            update.message.reply_text("Cooking link is not vaild, please input again!")
    else:
        update.message.reply_text("Cooking link is missing, please input again!")

def tvshow_write(update, context):
    message = update.message
    if message is None:
        query = update.callback_query
        if query.data == str(TVSHOW_WRITE):
            context.bot.send_message(chat_id=update.effective_chat.id, 
                                        text='Please share the review of this tv show')
            return TVSHOW_WRITE
        elif query.data == str(TVSHOW_END):
            context.bot.send_message(chat_id=update.effective_chat.id, 
                                        text="Click /start to try again")
            return ConversationHandler.END
    elif message.text is not None:
        global tvReview
        tvshow_data = {
            "link" : tvReview["link"],
            "id" : message.chat.id,
            "review" : message.text
        }
        redis_conn.lpush("tvshow", json.dumps(tvshow_data))
        update.message.reply_text("Thank you for your share, Click /start to try again")
        return ConversationHandler.END
    else:
        update.message.reply_text("Your review is missing, please input again!")
   
def hiking_options(update, context):
    query = update.callback_query
    if query.data == str(HIKING_READ):
        return hiking_read(update, context)
    elif query.data == str(HIKING_WRITE):
        message = "Please share photo and input route information in the photo caption"
        context.bot.send_message(chat_id=update.effective_chat.id,  text=message)
        return int(query.data)

def cooking_options(update, context):
    query = update.callback_query
    if query.data == str(COOKING_READ):
        return cooking_read(update, context)
    elif query.data == str(COOKING_WRITE):
        message = "Please upload cooking video or share the cooking video link"
        context.bot.send_message(chat_id=update.effective_chat.id,  text=message)
        return int(query.data)
    
def get_read_write_option(read_text, write_text, read, write):
    reply_keyboard_markup = InlineKeyboardMarkup(
        [
            [
            InlineKeyboardButton(
                text=read_text, callback_data=read),
            InlineKeyboardButton(
                text=write_text, callback_data=write)
            ]
        ]
    )
    return reply_keyboard_markup

def cancel(update, context):
    print('cancel invoke')
    ConversationHandler.END
    hiking_entrance(update, context)

def hiking_conv_handler():
    conv_handler = ConversationHandler(
    entry_points=[CommandHandler('hiking', hiking_entrance)],
    states={
        HIKING_OPTIONS: [CallbackQueryHandler(hiking_options)],
        HIKING_READ: [MessageHandler(Filters.text, hiking_read)],
        HIKING_WRITE: [MessageHandler(Filters.all, hiking_write)],
        HIKING_READ_PHOTO: [CallbackQueryHandler(hiking_photo)]
    },
    fallbacks=[CommandHandler('cancel', cancel)]
    )
    return conv_handler

def tv_show_conv_handler():
    conv_handler = ConversationHandler(
    entry_points=[CommandHandler('tvshow', tvshow_read)],
    states={
        TVSHOW_READ_PHOTO: [CallbackQueryHandler(tvshow_photo)],
        TVSHOW_WRITE_PROMPT: [CallbackQueryHandler(tvshow_write)],
        TVSHOW_WRITE: [MessageHandler(Filters.text, tvshow_write)]
    },
    fallbacks=[CommandHandler('cancel', cancel)]
    )
    return conv_handler

def cook_conv_handler():
    conv_handler = ConversationHandler(
    entry_points=[CommandHandler('cooking', cooking_entrance)],
    states={
        COOKING_OPTIONS: [CallbackQueryHandler(cooking_options)],
        COOKING_READ: [MessageHandler(Filters.text, cooking_read)],
        COOKING_WRITE: [MessageHandler(Filters.all, cooking_write)],
        COOKING_READ_VIDEO: [CallbackQueryHandler(cooking_video)]
    },
    fallbacks=[CommandHandler('cancel', cancel)]
    )
    return conv_handler

def welcome(update, context):
    welcome_message = '''Hello and welcome, {}.
I'm your leisure activity chatbot assistant and provide you 3 functions.
send /hiking to check or share hiking route and photos
send /tvshow to read or write review to TV show in Neflex
send /cooking to view or share the cooking video from youtube'''.format(
        update.message.from_user.first_name)
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=welcome_message)
    return ConversationHandler.END

def error_handler(update, context):
    logging.warning('Update "%s" caused error "%s"', update, context.error)
    context.bot.send_message(chat_id=update.message.chat_id, text="Sorry, an error occurred.")


def main() -> None:
    updater = Updater(token=(os.environ['ACCESS_TOKEN']), use_context=True)
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    dispatcher = updater.dispatcher
    default_handler = MessageHandler(Filters.all, welcome)
    dispatcher.add_handler(hiking_conv_handler())
    dispatcher.add_handler(tv_show_conv_handler())
    dispatcher.add_handler(cook_conv_handler())
    dispatcher.add_handler(default_handler)
    dispatcher.add_error_handler(error_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
