#!/bin/sh

echo "Running spider..."
sleep 15
#sanic-admin main.py
watchexec -e py,html,css,png,jpg,ico,txt,sh -r -s SIGKILL python main.py