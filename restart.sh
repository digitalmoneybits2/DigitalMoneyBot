#!/bin/bash
# pgrep python3 | grep -v $$ | xargs kill -9
kill $(pgrep -f 'tipbot.py')
python3 tipbot.py
