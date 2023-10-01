#!/bin/bash
echo
echo "Going to run SpotBot in the background using tmux..."
echo

if [ ! -f "spotbot/spotbot_config.pkl" ]; then
    echo
    echo "spotbot_config.pkl not found. Please manually run spotbot.py and fill in the required information!"
    echo "Then hit Ctrl+C to stop it and then run this script again."
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
    echo "Please run as root"
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
ExecStart=$(pwd)/spotbot/bin/python $(pwd)/spotbot/spotbot.py
Restart=always
RestartSec=3
User=$USERNAME
Group=$GROUP

[Install]
WantedBy=multi-user.target
EOL

systemctl daemon-reload
systemctl enable spotbot
systemctl start spotbot

echo "Service created as spotbot. You can now start and manage it using 'systemctl'."
