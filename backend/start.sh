#!/bin/bash

# FastAPIをリロードモードで起動
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &

# Discord Botを自動再起動モードで起動
# app/ フォルダ内の変更を監視して、bot.py を再起動する
watchfiles "python -u -m app.bot" app/
