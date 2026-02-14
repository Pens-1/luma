#!/bin/bash
# バックグラウンドでAPIを起動
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# フォアグラウンドでシンプルBotを起動
python3 app/bot.py
