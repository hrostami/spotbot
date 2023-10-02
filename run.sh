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

get_spotbot_add_service() {
    echo
    yellow "Going to update and run SpotBot in the background..."
    echo

    if [ ! -f "spotbot/spotbot_config.pkl" ]; then
        echo
        rred "spotbot_config.pkl not found. Please manually run spotbot.py and fill in the required information!"
        rred "Then hit Ctrl+C to stop it and then run this script again."
        echo
        exit 0
    fi

    if ! command -v tmux &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y tmux
    fi

    if [ ! -d "spotbot" ]; then
        git clone https://github.com/hrostami/spotbot.git
        cd spotbot
    else
        cd spotbot
        git pull origin
    fi

    sudo apt install python3-venv

    clear

    if [ ! -d "bin" ]; then
        python3 -m venv spotbot
    fi

    source bin/activate
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

    USERNAME=$(logname)

    GROUP=$(id -gn $USERNAME)

    SERVICE_FILE="/etc/systemd/system/spotbot.service"
    cat <<EOL > $SERVICE_FILE
[Unit]
Description=Spotbot Python Script

[Service]
ExecStart=$(pwd)/spotbot/bin/python3 $(pwd)/spotbot/spotbot.py
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

    yellow "Service created as spotbot. You can now start and manage it using 'systemctl'."

}


print_menu() {
    yellow "Menu:"
    green "1) Install and create service"
    green "2) Restart service"
    green "3) Show log in real time"
    red "4) Exit"
}

echo
bblue "Welcome to SpotBot Management Script"
echo

while true; do
    print_menu
    read -p "Enter your choice (1-4): " choice

    case $choice in
        1)
            echo
            echo "Installing and creating service..."
            get_spotbot_add_service
            readp "Press Enter to continue..."
            ;;
        2)
            echo
            yellow "Restarting service..."
            systemctl restart spotbot
            readp "Press Enter to continue..."
            ;;
        3)
            echo
            yellow "Showing log in real time. Press Ctrl+C to exit."
            sudo journalctl -u spotbot -f
            readp "Press Enter to continue..."
            ;;
        4)
            echo "Exiting."
            exit 0
            ;;
        *)
            echo "Invalid choice. Please choose a valid option."
            ;;
    esac
done