#!/bin/bash
set -e

# 複数データベースを作成する初期化スクリプト
# n8n, dify, fastapi 用のデータベースを作成

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- n8n用データベース
    CREATE DATABASE n8n;
    
    -- Dify用データベース
    CREATE DATABASE dify;
    
    -- Dify Plugin用データベース
    CREATE DATABASE dify_plugin;
    
    -- FastAPI用データベース
    CREATE DATABASE fastapi;
    
    -- 確認
    \l
EOSQL

echo "データベース初期化完了: n8n, dify, dify_plugin, fastapi"
