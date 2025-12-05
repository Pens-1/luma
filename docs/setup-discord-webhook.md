# Discord Webhook 設定手順

このドキュメントでは、n8n で Discord Webhook を使用して通知を送る設定手順を解説します。

## 前提条件

- Discord アカウントを持っていること
- 通知を送りたい Discord サーバー（ギルド）の管理権限があること

## 手順 1: Discord サーバーでウェブフックを作成

### 1.1 サーバー設定を開く

1. Discord アプリで、通知を送りたいサーバーを選択
2. サーバー名を右クリック → 「サーバー設定」をクリック

### 1.2 ウェブフック設定を開く

1. 左メニュー → 「連携サービス」をクリック
2. 「ウェブフック」タブを選択
3. 「新しいウェブフック」ボタンをクリック

### 1.3 ウェブフックを設定

**ウェブフック名**: `Schedule Optimizer`（任意）

**チャンネル**: 通知を送りたいチャンネルを選択

- 例: `#general`、`#schedule`、`#bot-notifications` など

**アバター画像**（オプション）:

- カスタム画像をアップロードできます
- ロボットやカレンダーのアイコンがおすすめ

### 1.4 Webhook URL をコピー

1. 「ウェブフック URL をコピー」ボタンをクリック
2. 以下のような形式の URL がコピーされます：

   ```
   https://discord.com/api/webhooks/1234567890/abcdefgh...
   ```

3. この URL を **必ず安全な場所に保存** してください

### 1.5 保存

「変更を保存」ボタンをクリックして設定を保存します。

## 手順 2: 環境変数に設定

### 2.1 .env ファイルを編集

プロジェクトルートの `.env` ファイルを開きます：

```bash
cd /home/user/repos/luma
nano .env  # または vi .env
```

### 2.2 Discord Webhook URL を設定

以下の行を編集します：

```bash
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/1234567890/abcdefgh...
```

保存してください。

### 2.3 Docker 環境に反映

n8n が起動中の場合は、再起動して環境変数を反映させます：

```bash
docker-compose restart n8n
```

または、停止して再起動：

```bash
docker-compose down
docker-compose up -d
```

## 手順 3: n8n で Discord 通知を設定

### 3.1 HTTP Request ノードを使用

n8n のワークフローで、Discord Webhook への通知は **HTTP Request** ノードで実装します。

**設定:**

- **Method**: `POST`
- **URL**: `={{ $env.DISCORD_WEBHOOK_URL }}`
- **Send Body**: `true`
- **Body Content Type**: `JSON`
- **Body (JSON)**:
  ```json
  {
    "content": "={{ $json.output }}"
  }
  ```

### 3.2 リッチメッセージ（Embed）を使う場合

Discord は「Embed」という形式でリッチなメッセージを送信できます：

**Body (JSON)**:

```json
{
  "embeds": [
    {
      "title": "🌅 今日の作戦",
      "description": "={{ $json.output }}",
      "color": 5814783,
      "footer": {
        "text": "Schedule Optimizer v0.1"
      },
      "timestamp": "={{ $now.toISO() }}"
    }
  ]
}
```

**カラーコードの例:**

- `3447003` - 青（#3498db）
- `15158332` - 赤（#e74c3c）
- `10181046` - 紫（#9b59b6）
- `5814783` - 緑（#58c9b9）
- `15844367` - オレンジ（#f39c12）

## Discord Webhook の仕様

### メッセージの制限

| 項目                      | 制限                         |
| ------------------------- | ---------------------------- |
| メッセージ本文（content） | 2,000 文字                   |
| Embed                     | 1 メッセージあたり最大 10 個 |
| Embed Title               | 256 文字                     |
| Embed Description         | 4,096 文字                   |
| Embed Fields              | 最大 25 個                   |

### レート制限

- 同じ Webhook URL に対して、**5 秒間に 5 リクエスト**まで
- Schedule Optimizer（1 日 1 回実行）では問題なし

## テスト方法

### curl でテスト

Webhook URL が正しく機能するか、curl でテストできます：

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"content": "テストメッセージ from Schedule Optimizer"}' \
  https://discord.com/api/webhooks/YOUR_WEBHOOK_URL
```

成功すると、Discord チャンネルにメッセージが表示されます。

### n8n でテスト

1. ワークフローを開く
2. 「Execute Workflow」ボタンをクリック
3. Discord チャンネルに通知が届くことを確認

## トラブルシューティング

### エラー: "Invalid Webhook Token"

**原因**: Webhook URL が正しくない、または削除/無効化されている

**対処法**:

1. Discord のサーバー設定 → 連携サービス → ウェブフック で URL を再確認
2. 必要に応じて新しい Webhook を作成
3. `.env` ファイルの URL を更新して `docker-compose restart n8n`

### エラー: "Unknown Webhook"

**原因**: Webhook URL の形式が間違っている

**対処法**:

1. URL が `https://discord.com/api/webhooks/` で始まっているか確認
2. URL の末尾に余計なスペースや改行がないか確認

### メッセージが送信されない

**原因**: 環境変数が正しく設定されていない

**対処法**:

1. `.env` ファイルに `DISCORD_WEBHOOK_URL` が設定されているか確認
2. `docker-compose.yml` で環境変数が注入されているか確認
3. n8n を再起動: `docker-compose restart n8n`

### Embed が正しく表示されない

**原因**: JSON 形式が間違っている

**対処法**:

1. [Discord Embed Visualizer](https://leovoel.github.io/embed-visualizer/) で JSON をテスト
2. n8n の「Expression Editor」で JSON が正しく生成されているか確認

## セキュリティ

### ✅ 推奨事項

- **Webhook URL は公開しない**: `.env` ファイルは `.gitignore` に追加済み
- **権限を最小限に**: Webhook を作成したチャンネル以外には投稿できません
- **定期的なローテーション**: セキュリティのため、定期的に Webhook を再作成

### ⚠️ Webhook が漏洩した場合

1. Discord のサーバー設定 → 連携サービス → ウェブフック
2. 問題の Webhook を削除
3. 新しい Webhook を作成
4. `.env` ファイルを更新

## 次のステップ

Discord Webhook の設定が完了したら、ワークフローを実行してテストしましょう。

- Slack と Discord の両方に通知を送る場合は、2 つの HTTP Request ノードを並列に配置できます
- 詳細は [ワークフロー設計ドキュメント](workflow-design.md) を参照してください
