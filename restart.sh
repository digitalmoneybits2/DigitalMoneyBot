#!/bin/bash
# pgrep python3 | grep -v $$ | xargs kill -9
kill $(pgrep -f 'python3 digitalmoneybot.py')
sleep 2
python3 digitalmoneybot.py
