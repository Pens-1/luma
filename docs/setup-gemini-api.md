# Google Gemini API 設定手順

このドキュメントでは、n8n で Google Gemini API を使用するための設定手順を解説します。

## 前提条件

- Google アカウントを持っていること

## 手順 1: Google AI Studio にアクセス

### 1.1 Google AI Studio を開く

[Google AI Studio](https://ai.google.dev/) にアクセスし、Google アカウントでログインします。

## 手順 2: API キーの取得

### 2.1 Get API Key をクリック

1. 画面右上または左メニューの「Get API key」をクリック
2. 「Create API key」をクリック

### 2.2 プロジェクトの選択

以下のいずれかを選択します：

**A. 既存のプロジェクトを使用する場合:**

- 「Create API key in existing project」を選択
- ドロップダウンから、先ほど作成した `schedule-optimizer` プロジェクトを選択
- 「Create」をクリック

**B. 新規プロジェクトを作成する場合:**

- 「Create API key in new project」を選択
- 「Create」をクリック

### 2.3 API キーをコピー

作成された API キーが表示されます：

```
AIzaSyD...（長い文字列）
```

**🔴 重要: この API キーを必ずコピーして安全な場所に保存してください**

## 手順 3: 環境変数に設定

### 3.1 .env ファイルを作成

プロジェクトルートで `.env.example` をコピーして `.env` を作成します。

```bash
cd /home/user/repos/luma
cp .env.example .env
```

### 3.2 API キーを設定

`.env` ファイルを開き、以下の行を編集します：

```bash
GOOGLE_GEMINI_API_KEY=AIzaSyD...（コピーしたAPIキー）
```

保存してください。

### 3.3 Docker 環境に反映

n8n が起動中の場合は、再起動して環境変数を反映させます：

```bash
docker-compose restart n8n
```

## 手順 4: n8n で Gemini Chat Model を設定

### 4.1 ワークフロー内でノードを追加

1. n8n 管理画面でワークフローを開く
2. 「+」ボタン → 「AI」カテゴリ → 「Google Gemini Chat Model」を選択

### 4.2 モデルの設定

**Credential for Google Gemini:**

- 「Create New Credential」をクリック
- **API Key**: `.env` に設定した `GOOGLE_GEMINI_API_KEY` の値を入力
  - または環境変数を参照: `{{ $env.GOOGLE_GEMINI_API_KEY }}`
- 「Save」をクリック

**Model Name:**

- `gemini-1.5-flash`（推奨: 高速で無料枠が豊富）
- または `gemini-1.5-pro`（より高精度だが無料枠が少ない）

**Temperature:**

- `0.7`（デフォルト、バランス重視）
- `0.3`（決定論的な出力が欲しい場合）
- `1.0`（創造的な出力が欲しい場合）

## Gemini API の無料枠について

### Gemini 1.5 Flash（推奨）

| 項目         | 無料枠            |
| ------------ | ----------------- |
| 入力トークン | 150 万トークン/分 |
| 出力トークン | 60 万トークン/分  |
| リクエスト数 | 1,500 回/分       |
| 1 日あたり   | 1,500 回          |

**🎯 Schedule Optimizer での使用量目安:**

- 1 回の実行で約 1,000 トークン（カレンダーデータ + プロンプト + レスポンス）
- 1 日 1 回実行なら、無料枠で十分運用可能

### Gemini 1.5 Pro

| 項目         | 無料枠            |
| ------------ | ----------------- |
| 入力トークン | 200 万トークン/分 |
| 出力トークン | 200 万トークン/分 |
| リクエスト数 | 50 回/分          |
| 1 日あたり   | 50 回             |

**注意**: リクエスト数の制限が厳しいため、頻繁に実行する場合は Flash を推奨。

## トラブルシューティング

### エラー: "API key not valid"

**原因**: API キーが正しく設定されていない

**対処法**:

1. Google AI Studio で API キーを再確認
2. `.env` ファイルの `GOOGLE_GEMINI_API_KEY` を確認
3. n8n を再起動して環境変数を反映: `docker-compose restart n8n`
4. n8n のクレデンシャル画面で API キーを再入力

### エラー: "Rate limit exceeded"

**原因**: 無料枠の制限を超えた

**対処法**:

1. Google AI Studio の [Quota](https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas) を確認
2. モデルを `gemini-1.5-flash` に変更（より大きい無料枠）
3. リトライロジックを追加（n8n の「Error Trigger」ノードで実装可能）

### エラー: "The API key doesn't have the required permissions"

**原因**: API キーのプロジェクトで Generative Language API が有効化されていない

**対処法**:

1. [GCP コンソール](https://console.cloud.google.com/) にアクセス
2. API キーのプロジェクトを選択
3. 「API とサービス」 → 「ライブラリ」
4. 「Generative Language API」を検索して有効化

## API キーのセキュリティ

### ✅ 推奨事項

- `.env` ファイルは `.gitignore` に追加されているため、リポジトリにコミットされません
- API キーは絶対に公開リポジトリにコミットしないでください
- 定期的に API キーをローテーション（再生成）してください

### 🔒 API キーの制限設定（推奨）

Google Cloud Console で API キーに制限を設定できます：

1. [認証情報](https://console.cloud.google.com/apis/credentials)を開く
2. 作成した API キーをクリック
3. 「アプリケーションの制限」:
   - 「HTTP リファラー」を選択（本番環境の場合）
   - `localhost:5678` を追加（開発環境の場合）
4. 「API の制限」:
   - 「キーを制限」を選択
   - 「Generative Language API」のみにチェック

## 次のステップ

Gemini API の設定が完了したら、[ワークフロー設計ドキュメント](workflow-design.md)を参照して、n8n でワークフローを作成しましょう。
