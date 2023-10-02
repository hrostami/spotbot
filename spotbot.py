import os
import asyncio
import threading
import concurrent.futures
import pickle
from spotdl import Spotdl, Song
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler

# File to store the allowed_ids and admin_id
pickle_file = 'spotbot_config.pkl'

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

def download_spotify_link(spotdl, link: str) -> list:
    songs = spotdl.search([link])
    if songs:
        return songs
    else:
        return []

def download_songs(spotdl, query):
    song, path = spotdl.download(query)
    print(f"\npath is :{path}\n")
    print(f'song is:\n{song}\n')
    return song, path

def run_spotdl_operations(link):
    spotdl = start_spotdl()
    songs = download_spotify_link(spotdl,link)
    if songs:
        song, path = download_songs(spotdl, songs[0])
    return song, path
# async def spotdl_async(link):
#     task1 = asyncio.create_task(download_spotify_link(link))
#     songs = await task1.result()
#     task2 = asyncio.create_task(download_songs_async(songs))

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

def download_song(song):
    if len(song.artists) > 1:
        artist = ''
        for singer in song.artists:
            artist += f"{singer}, "
        artist = artist[:-2]
    else:
        artist = song.artist
    name = song.name
    file_path = artist + ' - ' + name
    os.system(f'spotdl {song.url}')
    return file_path

def find_mp3_by_artist(artist):
    mp3_files = [file for file in os.listdir() if file.endswith('.mp3') and file.startswith(artist)]
    return mp3_files

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Hello! Send a Spotify link and I'll download the corresponding audio.")

def button_click(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    user_id = int(query.data.split('_')[1])

    if query.data.startswith('approve'):
        allowed_ids.append(user_id)
        save_allowed_ids()

        context.bot.send_message(chat_id=user_id, text='Your request has been approved. You can now use the bot.')

        query.edit_message_text(text=f'User {user_id} approved!')

    elif query.data.startswith('deny'):
        context.bot.send_message(chat_id=user_id, text='Your request to use this bot has been denied.')
        query.edit_message_text(text=f'User {user_id} denied access.')

def handle_messages(update: Update, context: CallbackContext):
    text = update.message.text
    user_id = update.message.from_user.id

    if user_id not in allowed_ids and user_id != admin_id:
        handle_new_user(update, context)
        return

    if text.startswith('https://open.spotify.com/') or text.startswith('https://spotify.link/'):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_spotdl_operations, text)
            song, path = future.result()
        songs = download_spotify_link(text)
        if songs: 
            for song in songs:
                threading.Thread(target=download_songs_async, args=(song,)).start()
                file_path = download_song(song)
                mp3_file_path = f'{file_path}.mp3'
                if os.path.exists(mp3_file_path):
                    with open(mp3_file_path, 'rb') as audio_file:
                        if len(songs) == 1:
                            context.bot.send_photo(user_id, song.cover_url, caption=file_path)
                        context.bot.send_audio(chat_id=user_id, audio=audio_file)
                    os.remove(mp3_file_path)
                else:
                    prob_song = find_mp3_by_artist(song.artist)
                    if prob_song:
                        context.bot.send_photo(user_id, song.cover_url, caption=file_path)
                        context.bot.send_audio(chat_id=user_id, audio=open(prob_song[0], 'rb'))
                        os.remove(prob_song)
        else:
            update.message.reply_text("Unable to download songs from the Spotify link you sent.")
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
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_messages))
    dispatcher.add_handler(CallbackQueryHandler(button_click))

    print("Bot is running...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()