# Notion API 設定ガイド

このガイドでは、n8n から Notion DB にアクセスして Todo を取得するための設定手順を説明します。

---

## 📋 目次

1. [Notion 統合（Integration）の作成](#1-notion統合integrationの作成)
2. [データベースの共有設定](#2-データベースの共有設定)
3. [環境変数の設定](#3-環境変数の設定)
4. [n8n でのクレデンシャル設定](#4-n8nでのクレデンシャル設定)
5. [データベース ID の取得](#5-データベースidの取得)
6. [トラブルシューティング](#トラブルシューティング)

---

## 1. Notion 統合（Integration）の作成

### 1-1. Notion 統合ページにアクセス

1. [Notion Integrations](https://www.notion.so/my-integrations) を開く
2. Notion アカウントでログイン

### 1-2. 新しい統合を作成

1. **「+ 新しい統合」** または **「New integration」** をクリック
2. 以下を入力：
   - **名前**: `Schedule Optimizer` （任意）
   - **ワークスペース**: Todo データベースがあるワークスペースを選択
   - **タイプ**: `Internal`（内部統合）のまま
3. **「送信」** または **「Submit」** をクリック

### 1-3. API シークレットをコピー

1. 統合が作成されたら、**「Secrets」** タブに自動的に移動します
2. **「Internal Integration Secret」** が表示されます
3. **「Show」** をクリックして、シークレットを表示
4. **「Copy」** をクリックしてコピー
   ```
   secret_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
   ```
5. このシークレットを安全な場所に保存しておく

> [!WARNING]
> このシークレットは **パスワードのようなもの** です。他人と共有しないでください。

---

## 2. データベースの共有設定

Notion のデータベースを Integration に共有する必要があります。

### 2-1. Todo データベースを開く

1. Notion で **Todo データベース** があるページを開く
2. データベースが表示されていることを確認

### 2-2. Integration に共有

1. データベースページの右上にある **「...」（3 点メニュー）** をクリック
2. **「接続」** または **「Connections」** を選択
3. 先ほど作成した統合（例：`Schedule Optimizer`）を検索
4. 統合名をクリックして接続を確認

これで、Integration がこのデータベースにアクセスできるようになります。

---

## 3. 環境変数の設定

### 3-1. `.env` ファイルを編集

プロジェクトルートの `.env` ファイルに以下を追加：

```bash
# Notion API設定
NOTION_API_SECRET=secret_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
NOTION_TODO_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

- `NOTION_API_SECRET`: 手順 1-3 でコピーしたシークレット
- `NOTION_TODO_DATABASE_ID`: 後述の手順 5 で取得するデータベース ID

### 3-2. `n8nに環境変数を渡す`

`.env.example` にも追加しておきます（テンプレート用）：

```bash
# Notion API設定
NOTION_API_SECRET=your_notion_integration_secret_here
NOTION_TODO_DATABASE_ID=your_database_id_here
```

---

## 4. n8n でのクレデンシャル設定

n8n には **2 つの方法** があります。環境変数を使う方法と、直接入力する方法です。

### 方法 A: 環境変数を使う（推奨）

1. n8n 管理画面の **「Credentials」** → **「Add Credential」**
2. **「Notion API」** を検索して選択
3. **API Key** に以下を入力：
   ```
   ={{ $env.NOTION_API_SECRET }}
   ```
4. **「Save」** をクリック

### 方法 B: 直接入力

1. n8n 管理画面の **「Credentials」** → **「Add Credential」**
2. **「Notion API」** を検索して選択
3. **API Key** に `.env` から `NOTION_API_SECRET` の値を **直接コピペ**
4. **「Save」** をクリック

---

## 5. データベース ID の取得

Notion データベースの ID を取得する方法は 2 つあります。

### 方法 A: URL から取得（簡単）

1. Notion で **Todo データベース** を開く
2. ブラウザのアドレスバーの URL を確認：
   ```
   https://www.notion.so/workspace/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx?v=...
   ```
3. `?` の前の **32 文字の英数字** がデータベース ID です
4. ハイフン（`-`）がある場合は削除してください

例：

```
URL: https://www.notion.so/myworkspace/a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6?v=xxx
データベースID: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

### 方法 B: Notion の Share 機能から取得

1. データベースページの右上 **「Share」** をクリック
2. **「Copy link」** でリンクをコピー
3. リンク内の 32 文字がデータベース ID

取得した ID を `.env` ファイルの `NOTION_TODO_DATABASE_ID` に設定してください。

---

## 6. n8n を再起動

環境変数を追加したら、n8n を再起動します：

```bash
docker-compose restart n8n
```

---

## トラブルシューティング

### エラー: "API key is invalid"

**原因**:

- API シークレットが間違っている
- 環境変数が正しく読み込まれていない

**解決策**:

1. `.env` ファイルの `NOTION_API_SECRET` を確認
2. n8n を再起動: `docker-compose restart n8n`
3. ブラウザをリロード（`Ctrl + Shift + R`）

---

### エラー: "Object not found"

**原因**:

- データベース ID が間違っている
- データベースが Integration に共有されていない

**解決策**:

1. データベース ID が正しいか確認
2. Notion でデータベースページを開き、**「...」→「Connections」** で統合が接続されているか確認

---

### データが取得できない

**確認ポイント**:

1. データベースに実際にデータが入っているか
2. フィルター条件が厳しすぎないか
3. n8n のクレデンシャルが正しく設定されているか

---

## データベースの推奨構造

以下のようなプロパティを持つ Todo データベースを推奨します：

| プロパティ名 | タイプ       | 説明                         |
| ------------ | ------------ | ---------------------------- |
| `Name`       | Title        | Todo のタイトル              |
| `Status`     | Select       | 状態（未着手、進行中、完了） |
| `Priority`   | Select       | 優先度（高、中、低）         |
| `Due Date`   | Date         | 期限                         |
| `Tags`       | Multi-select | カテゴリやタグ               |

---

## 次のステップ

1. ✅ Notion 統合作成
2. ✅ データベース共有
3. ✅ 環境変数設定
4. ⏭️ [Notion Todo 取得ワークフローをインポート](../n8n/workflows/)
5. ⏭️ テスト実行

設定完了後は、n8n で Notion ノードを使ってデータベースから Todo を取得できます！
