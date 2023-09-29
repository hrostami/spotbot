#!/bin/bash

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
else
    cd spotbot
    git pull origin master
    cd ..
fi

sudo apt install python3-venv

clear

if [ ! -d "spotbot" ] || [ ! -d "spotbot/bin" ]; then
    python3 -m venv spotbot
fi

source spotbot/bin/activate
pip install --upgrade python-telegram-bot==13.5 spotdl

if ! command -v ffmpeg &> /dev/null; then
    sudo apt-get install -y ffmpeg
fi

tmux has-session -t spotbot 2>/dev/null
if [ $? != 0 ]; then
    tmux new-session -d -s spotbot "python3 spotbot.py"
else
    tmux kill-session -t spotbot
    tmux new-session -d -s spotbot "python3 spotbot.py"
fi
