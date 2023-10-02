import os
import pickle

# File to store the allowed_ids and admin_id
pickle_file = '/root/spotbot/spotbot_config.pkl'

def save_allowed_ids():
    data = {'allowed_ids': allowed_ids,
            'admin_id': admin_id,
            'spotdl_client_id': spotdl_client_id,
            'spotdl_client_secret': spotdl_client_secret,
            'telegram_bot_token': telegram_bot_token,
            }
    with open(pickle_file, 'wb') as f:
        pickle.dump(data, f)

# Initialize allowed_ids and admin_id from pickle if available, else start fresh
allowed_ids = []
admin_id = int(input("Enter the admin's Telegram user ID: "))
telegram_bot_token = input("\nEnter Telegram Bot Token from @Botfather: ")
spotify_cred = input("\nDo you want to use your own spotify credentials (y/n): ")
if spotify_cred == 'y':
    spotdl_client_id = input("\n Enter your Spotify client ID: ")
    spotdl_client_secret = input("\n Enter your Spotify client secret: ")
elif spotify_cred == 'n':
    spotdl_client_id = '5f573c9620494bae87890c0f08a60293'
    spotdl_client_secret = '212476d9b0f3472eaa762d90b19b0ba8'
save_allowed_ids()