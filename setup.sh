#!/bin/bash

# LUMA Setup Script v0.5

echo "🚀 Starting LUMA infrastructure setup..."

# 1. .envファイルの作成
if [ ! -f .env ]; then
    echo "📄 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️ .env file created. Please edit it with your API keys if needed."
else
    echo "✅ .env file already exists."
fi

# 2. 必要なディレクトリの作成（Postgresの初期化用など）
mkdir -p postgres/data n8n/workflows backend/app

# 3. Dockerコンテナの起動
echo "🐳 Starting Docker containers..."
docker compose up -d

echo "------------------------------------------------"
echo "✅ Infrastructure is booting up!"
echo ""
echo "🔗 n8n: http://localhost:5678"
echo "🔗 Python Worker (FastAPI): http://localhost:8001/docs"
echo "🔗 Dify: http://localhost"
echo ""
echo "Next step: Install Aider and OpenClaw on your WSL host."
echo "------------------------------------------------"
