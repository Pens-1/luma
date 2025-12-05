# Schedule Optimizer v0.1

**n8n + Gemini API による予定最適化エージェント**

Google カレンダーの予定を毎朝自動取得し、Gemini AI が空き時間を分析して効率的なタスク配分を提案するシステムです。

## 🎯 機能

- 毎朝 8:00 に自動実行（Schedule Trigger）
- Google カレンダーから今日の予定を取得
- Gemini 1.5 Flash が空き時間を分析してタスクを提案
- Discord（または Slack）に最適化された予定を通知

## 🛠 技術スタック

- **n8n**: ワークフローオーケストレーション（Docker 環境）
- **Google Gemini 1.5 Flash**: AI 分析エンジン（無料枠利用）
- **Google Calendar API**: 予定データ取得
- **Discord Webhook**: 通知先（Slack も対応可能）

## 🚀 クイックスタート

### 1. リポジトリのクローン

```bash
git clone git@github.com:Pens-1/luma.git
cd luma
```

### 2. 環境変数の設定

`.env.example` をコピーして `.env` を作成し、必要な値を設定します。

```bash
cp .env.example .env
# エディタで .env を開いて、APIキーなどを設定
```

### 3. Docker 起動

```bash
docker-compose up -d
```

n8n が起動したら、ブラウザで `http://localhost:5678` にアクセスします。

### 4. クレデンシャル設定

n8n 管理画面で以下のクレデンシャルを設定します：

1. **Google Calendar (OAuth2)** - [設定手順](docs/setup-google-api.md)
2. **Google Gemini API** - [設定手順](docs/setup-gemini-api.md)
3. **Discord Webhook** - [設定手順](docs/setup-discord-webhook.md)（または Slack Incoming Webhook）

### 5. ワークフローのインポート

1. n8n 管理画面の「Workflows」→「Import from File」をクリック
2. `n8n/workflows/schedule-optimizer-v0.1.json` を選択
3. ワークフローが開いたら、各ノードのクレデンシャルを設定
4. 「Execute Workflow」ボタンで手動テスト実行

## 📚 ドキュメント

- [Google Calendar API 設定手順](docs/setup-google-api.md)
- [Gemini API 設定手順](docs/setup-gemini-api.md)
- [Discord Webhook 設定手順](docs/setup-discord-webhook.md)
- [ワークフロー設計詳細](docs/workflow-design.md)

## 🔧 開発

### n8n のログ確認

```bash
docker-compose logs -f n8n
```

### n8n の再起動

```bash
docker-compose restart n8n
```

### 完全クリーンアップ

```bash
docker-compose down -v
```

## 📝 今後の拡張案

- [ ] Notion 連携（タスク自動登録）
- [ ] Google Tasks 連携
- [ ] 週間レポート生成
- [ ] タスク優先度の学習機能
- [ ] 複数カレンダーの統合サポート

## 📄 ライセンス

MIT

## 🙋 サポート

質問や問題があれば、GitHub の Issues でお知らせください。
