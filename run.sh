#!/bin/bash

red='\033[0;31m'
bblue='\033[0;34m'
yellow='\033[0;33m'
green='\033[0;32m'
plain='\033[0m'
red(){ echo -e "\033[31m\033[01m$1\033[0m";}
green(){ echo -e "\033[32m\033[01m$1\033[0m";}
yellow(){ echo -e "\033[33m\033[01m$1\033[0m";}
blue(){ echo -e "\033[36m\033[01m$1\033[0m";}
white(){ echo -e "\033[37m\033[01m$1\033[0m";}
bblue(){ echo -e "\033[34m\033[01m$1\033[0m";}
rred(){ echo -e "\033[35m\033[01m$1\033[0m";}
readtp(){ read -t5 -n26 -p "$(yellow "$1")" $2;}
readp(){ read -p "$(yellow "$1")" $2;}

cd
# Get/update spotbot
if [ ! -d "spotbot" ]; then
    git clone https://github.com/hrostami/spotbot.git
else
    cd spotbot
    git pull origin
    cd
fi

set_bot_credentials() {
    if [ -f "spotbot/spotbot_config.pkl" ]; then
        readp "Config already exists, do you want to replace it? (y/n): " choice
        if [[ $choice =~ ^[Yy] ]]; then
            :
        else
            return
        fi
    fi
    
    yellow "--------------Getting credntials--------------"
    python3 <<EOF
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
EOF
    yellow "----------------------------------------------"
    readp "Press Enter to continue..."
}
get_spotbot_add_service() {
    echo
    yellow "Going to update and run SpotBot in the background..."
    echo

    if [ ! -f "spotbot/spotbot_config.pkl" ]; then
        echo
        rred "spotbot_config.pkl not found. Please set credentials..."
        echo
        set_bot_credentials
    fi

    sudo apt install python3-venv -y

    clear
    cd spotbot

    if [ ! -d "spotbot-venv" ]; then
        python3 -m venv spotbot-venv
    fi

    source spotbot-venv/bin/activate
    pip install --upgrade python-telegram-bot==13.5 spotdl

    if ! command -v ffmpeg &> /dev/null; then
        sudo apt-get install -y ffmpeg
    fi

    clear

    # Check if the script is run with superuser privileges
    if [ "$EUID" -ne 0 ]; then
        rred "Please run as root"
        exit
    fi

    cd
    SERVICE_NAME="spotbot"

    if systemctl list-units --type=service | grep -q "\<$SERVICE_NAME\>"; then
        yellow "Service '$SERVICE_NAME' exists."
        systemctl restart spotbot

    else
        rred "Service '$SERVICE_NAME' does not exist."
        USERNAME=$(logname)

        GROUP=$(id -gn $USERNAME)

        SERVICE_FILE="/etc/systemd/system/spotbot.service"
        cat <<EOL > $SERVICE_FILE
[Unit]
Description=Spotbot Python Script

[Service]
ExecStart=$(pwd)/spotbot/spotbot-venv/bin/python3 $(pwd)/spotbot/spotbot.py
Restart=always
RestartSec=3
User=$USERNAME
Group=$GROUP
WorkingDirectory=$(pwd)/spotbot

[Install]
WantedBy=multi-user.target
EOL

        systemctl daemon-reload
        systemctl enable spotbot
        systemctl start spotbot

    fi

    yellow "Service created as spotbot. You can now start and manage it using 'systemctl'."

}


print_menu() {
    bblue "   _____                __   ____          __ ";
    bblue "  / ___/ ____   ____   / /_ / __ ) ____   / /_";
    bblue "  \__ \ / __ \ / __ \ / __// __  |/ __ \ / __/";
    bblue " ___/ // /_/ // /_/ // /_ / /_/ // /_/ // /_  ";
    bblue "/____// .___/ \____/ \__//_____/ \____/ \__/  ";
    bblue "     /_/                                      ";
    white "               Created by Hosy                "
    white "----------------------------------------------"
    white "      Github: https://github.com/hrostami"
    white "      Twitter: https://twitter.com/hosy000"
    echo
    yellow "-------------------Menu------------------"
    green "1. Set Credntials"
    echo
    green "2. Start SpotBot and create service"
    echo
    green "3. Restart SpotBot"
    echo
    green "4. Show log in real time"
    echo
    green "5. Stop SpotBot"
    echo
    red "0. Exit"
    yellow "-----------------------------------------"
}

while true; do
    clear
    print_menu
    readp "Enter your choice (1-5): " choice

    case "$choice" in
        1)
            yellow "Going to create required credntials for you"
            set_bot_credentials
            ;;
        2)
            echo
            rred "Installing and creating service..."
            get_spotbot_add_service
            readp "Press Enter to continue..."
            ;;
        3)
            echo
            rred "Restarting service..."
            systemctl restart spotbot
            echo
            readp "Press Enter to continue..."
            ;;
        4)
            echo
            rred "Showing log in real time. Press Ctrl+C to exit."
            echo
            sudo journalctl -u spotbot -f
            echo
            readp "Press Enter to continue..."
            ;;
        5)
            echo
            rred "Stoping service..."
            systemctl stop spotbot
            echo
            rred "Done!"
            echo
            readp "Press Enter to continue..."
            ;;
        0)
            echo "Exiting."
            exit 0
            ;;
        *)
            echo "Invalid choice. Please choose a valid option."
            ;;
    esac
done