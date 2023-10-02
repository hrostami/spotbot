import os
import threading
import asyncio
import concurrent.futures
import pickle
from spotdl import Spotdl, Song
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler

# File to store the allowed_ids and admin_id
pickle_file = 'spotbot_config.pkl'

executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

# Initialize allowed_ids and admin_id from pickle if available, else start fresh
if os.path.exists(pickle_file):
    with open(pickle_file, 'rb') as f:
        data = pickle.load(f)
        allowed_ids = data.get('allowed_ids', [])
        admin_id = data.get('admin_id', None)
        spotdl_client_id = data.get('spotdl_client_id', '5f573c9620494bae87890c0f08a60293')
        spotdl_client_secret = data.get('spotdl_client_secret', '212476d9b0f3472eaa762d90b19b0ba8')
        telegram_bot_token = data.get('telegram_bot_token', None)

else:
    allowed_ids = []
    admin_id = None
    spotdl_client_id = '5f573c9620494bae87890c0f08a60293'
    spotdl_client_secret = '212476d9b0f3472eaa762d90b19b0ba8'
    telegram_bot_token =  None

def save_allowed_ids():
    data = {'allowed_ids': allowed_ids,
            'admin_id': admin_id,
            'spotdl_client_id': spotdl_client_id,
            'spotdl_client_secret': spotdl_client_secret,
            'telegram_bot_token': telegram_bot_token,
            }
    with open(pickle_file, 'wb') as f:
        pickle.dump(data, f)

def start_spotdl():
    spotdl_instance = Spotdl(
        client_id=spotdl_client_id,
        client_secret=spotdl_client_secret
    )
    return spotdl_instance
spotdl = None

def run_spotdl_operations(link, mode=''):
    global spotdl
    if not spotdl:
        spotdl = start_spotdl()
    songs = spotdl.search([link])
    if mode == 'search':
        return songs
    else:
        if songs:
            results = spotdl.download_songs(songs)
            return results
        else:
            return []

# Function to handle new users
def handle_new_user(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_name = update.message.from_user.username

    # Send a message to the admin to approve the user
    admin_message = f"New user: @{user_name} (ID: {user_id}). Do you want to allow this user?"
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data=f'approve_{user_id}'),
         InlineKeyboardButton("No", callback_data=f'deny_{user_id}')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    context.bot.send_message(chat_id=admin_id, text=admin_message, reply_markup=reply_markup)

    update.message.reply_text("Your request to use this bot has been sent to the admin. Please wait.")

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Hello!\nSend a Spotify link \nor\nsearch 'Artist - Song' ")

def button_click(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    user_id = int(query.data.split('_')[-1])

    if query.data.startswith('search_result_yes'):
        link = query.data.split('_')[-2]
        query.edit_message_text(text=f'Downloading the song...')
        future = executor.submit(run_spotdl_operations, link)
        songs = future.result()
        if songs: 
            for item in songs:
                song = item[0]
                name = song.artist + ' - ' + song.name
                mp3_file_path = item[1]
                if os.path.exists(mp3_file_path):
                    with open(mp3_file_path, 'rb') as audio_file:
                        if len(songs) == 1:
                            context.bot.send_photo(user_id, song.cover_url, caption=name)
                        context.bot.send_audio(chat_id=user_id, audio=audio_file)
                    os.remove(mp3_file_path)
    elif query.data.startswith('search_result_no'):
        query.edit_message_text(text=f'Download cancelled.')

    elif query.data.startswith('approve'):
        allowed_ids.append(user_id)
        save_allowed_ids()

        context.bot.send_message(chat_id=user_id, text='Your request has been approved. You can now use the bot.')

        query.edit_message_text(text=f'User {user_id} approved!')

    elif query.data.startswith('deny'):
        context.bot.send_message(chat_id=user_id, text='Your request to use this bot has been denied.')
        query.edit_message_text(text=f'User {user_id} denied access.')

def search_and_confirm(update: Update, context: CallbackContext, artist, name, link):
    user_id = update.message.from_user.id
    search_result = f"{artist} - {name}"
    
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data=f'search_result_yes_{link}_{user_id}'),
         InlineKeyboardButton("No", callback_data=f'search_result_no_{user_id}')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(f"Search result:\n{search_result}.\n\n Is this correct?", reply_markup=reply_markup)


def handle_messages(update: Update, context: CallbackContext):
    text = update.message.text
    user_id = update.message.from_user.id

    if user_id not in allowed_ids and user_id != admin_id:
        handle_new_user(update, context)
        return

    if text.startswith('https://open.spotify.com/') or text.startswith('https://spotify.link/'):
        update.message.reply_text("Processing the link you sent.")
        future = executor.submit(run_spotdl_operations, text)
        songs = future.result()
        if songs: 
            for item in songs:
                song = item[0]
                name = song.artist + ' - ' + song.name
                mp3_file_path = item[1]
                if os.path.exists(mp3_file_path):
                    with open(mp3_file_path, 'rb') as audio_file:
                        if len(songs) == 1:
                            context.bot.send_photo(user_id, song.cover_url, caption=name)
                        context.bot.send_audio(chat_id=user_id, audio=audio_file)
                    os.remove(mp3_file_path)
        else:
            update.message.reply_text("Unable to download songs from the Spotify link you sent.")
    elif '-' in text:
        future = executor.submit(run_spotdl_operations, text, 'search')
        song = future.result()[0]
        search_and_confirm(update, context, song.artist, song.name, text)
    else:
        update.message.reply_text("Wrong link! This bot is only for downloading songs from Spotify!")

def list_allowed_users(update: Update, context: CallbackContext):
    if update.message.from_user.id == admin_id:
        allowed_users_info = ""
        for user_id in allowed_ids:
            user = context.bot.get_chat(user_id)
            allowed_users_info += f"User ID: {user_id}, Username: @{user.username}\n" if user.username else f"User ID: {user_id}\n\n"

        if allowed_users_info:
            update.message.reply_text("List of allowed users:\n" + allowed_users_info)
        else:
            update.message.reply_text("No users are currently allowed.")
    else:
        update.message.reply_text("You are not authorized to perform this action.")

def delete_user(update: Update, context: CallbackContext):
    if update.message.from_user.id == admin_id:
        user_id = int(context.args[0])
        if user_id in allowed_ids:
            user = context.bot.get_chat(user_id)
            allowed_ids.remove(user_id)
            save_allowed_ids()
            update.message.reply_text(f"User ID {user_id}, Username: @{user.username}, has been removed from the allowed list." if user.username else f"User ID {user_id} has been removed from the allowed list.")
        else:
            update.message.reply_text(f"User ID {user_id} is not in the allowed list.")
    else:
        update.message.reply_text("You are not authorized to perform this action.")

def send_message_to_users(update: Update, context: CallbackContext):
    message = update.message.text[9:]
    if update.message.from_user.id == admin_id:
        for user_id in allowed_ids:
            user = context.bot.get_chat(user_id)
            allowed_users_info += f"User ID: {user_id}, Username: @{user.username}\n" if user.username else f"User ID: {user_id}\n\n"

        if allowed_users_info:
            update.message.reply_text(f'Message sent:\n{message}')
        else:
            update.message.reply_text("No users are currently allowed.")
    else:
        update.message.reply_text("You are not authorized to perform this action.")

def main():
    global allowed_ids, admin_id, spotdl_client_id, spotdl_client_secret, telegram_bot_token

    if admin_id is None:
        admin_id = int(input("Enter the admin's Telegram user ID: "))
        telegram_bot_token = input("\nEnter Telegram Bot Token from @Botfather: ")
        spotify_cred = input("\nDo you want to use your own spotify credentials (y/n): ")
        if spotify_cred == 'y':
            spotdl_client_id = input("\n Enter your Spotify client ID: ")
            spotdl_client_secret = input("\n Enter your Spotify client secret: ")
        save_allowed_ids()

    updater = Updater(token=telegram_bot_token, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("listusers", list_allowed_users))
    dispatcher.add_handler(CommandHandler("deleteuser", delete_user, pass_args=True))
    dispatcher.add_handler(CommandHandler("send_message", send_message_to_users, pass_args=True))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_messages))
    dispatcher.add_handler(CallbackQueryHandler(button_click))

    print("Bot is running...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()