# Google Calendar API 設定手順

このドキュメントでは、n8n で Google Calendar API を使用するための設定手順を解説します。

## 前提条件

- Google アカウントを持っていること
- Google カレンダーを使用していること

## 手順 1: Google Cloud Platform (GCP) プロジェクトの作成

### 1.1 GCP コンソールにアクセス

[Google Cloud Console](https://console.cloud.google.com/) にアクセスし、Google アカウントでログインします。

### 1.2 新規プロジェクトを作成

1. 画面上部の「プロジェクトを選択」をクリック
2. 「新しいプロジェクト」を選択
3. プロジェクト名: `schedule-optimizer`（任意）
4. 「作成」をクリック

## 手順 2: Google Calendar API の有効化

### 2.1 API ライブラリを開く

1. 左メニュー → 「API とサービス」 → 「ライブラリ」
2. 検索バーに「Google Calendar API」と入力
3. 「Google Calendar API」を選択
4. 「有効にする」をクリック

## 手順 3: OAuth 同意画面の設定

### 3.1 OAuth 同意画面を開く

1. 左メニュー → 「API とサービス」 → 「OAuth 同意画面」
2. User Type: **外部** を選択（個人利用の場合）
3. 「作成」をクリック

### 3.2 アプリ情報を入力

**アプリ情報:**

- アプリ名: `Schedule Optimizer`
- ユーザーサポートメール: あなたのメールアドレス
- デベロッパーの連絡先情報: あなたのメールアドレス

「保存して次へ」をクリック

### 3.3 スコープの追加

1. 「スコープを追加または削除」をクリック
2. フィルタに「calendar」と入力
3. 以下をチェック:
   - `https://www.googleapis.com/auth/calendar` (カレンダーの読み書き)
   - または `https://www.googleapis.com/auth/calendar.readonly` (読み取り専用)
4. 「更新」→「保存して次へ」

### 3.4 テストユーザーの追加

1. 「ADD USERS」をクリック
2. あなたの Google アカウントのメールアドレスを追加
3. 「保存して次へ」

## 手順 4: OAuth 2.0 クレデンシャルの作成

### 4.1 クレデンシャル画面を開く

1. 左メニュー → 「API とサービス」 → 「認証情報」
2. 「認証情報を作成」 → 「OAuth 2.0 クライアント ID」

### 4.2 アプリケーションの種類を選択

- アプリケーションの種類: **ウェブアプリケーション**
- 名前: `n8n-schedule-optimizer`

### 4.3 承認済みのリダイレクト URI を設定

> **🔴 重要: n8n の Redirect URI を正確に設定する必要があります**

1. n8n 管理画面を開く (`http://localhost:5678`)
2. 左メニュー → 「Credentials」 → 「Add Credential」
3. 「Google Calendar OAuth2 API」を選択
4. 画面に表示される **OAuth Redirect URL** をコピー

   - 例: `http://localhost:5678/rest/oauth2-credential/callback`

5. GCP コンソールに戻り、「承認済みのリダイレクト URI」に貼り付け
6. 「作成」をクリック

### 4.4 クライアント ID とシークレットを保存

作成後、以下が表示されます：

- **クライアント ID**: `1234567890-abcdef...apps.googleusercontent.com`
- **クライアントシークレット**: `GOCSPX-...`

これらを **必ずコピーして保存** してください（次の手順で使用します）。

## 手順 5: n8n でクレデンシャルを設定

### 5.1 n8n の Credentials 画面を開く

1. n8n 管理画面 (`http://localhost:5678`)
2. 左メニュー → 「Credentials」
3. 「Add Credential」 → 「Google Calendar OAuth2 API」

### 5.2 クレデンシャル情報を入力

- **Credential Name**: `Google Calendar`（任意）
- **Client ID**: 手順 4.4 でコピーしたクライアント ID
- **Client Secret**: 手順 4.4 でコピーしたクライアントシークレット

### 5.3 OAuth 認証を実行

1. 「Connect my account」ボタンをクリック
2. Google アカウントでログイン
3. 権限の確認画面で「許可」をクリック
4. n8n にリダイレクトされ、「Connected」と表示されれば OK

### 5.4 保存

「Save」ボタンをクリックしてクレデンシャルを保存します。

## トラブルシューティング

### エラー: "Redirect URI mismatch"

**原因**: GCP に設定した Redirect URI と n8n の Redirect URI が一致していない

**対処法**:

1. n8n のクレデンシャル画面で表示される Redirect URL を再確認
2. GCP コンソール → 認証情報 → OAuth 2.0 クライアント ID を編集
3. Redirect URI を正確に一致させる（末尾のスラッシュなども含めて完全一致）

### エラー: "Access blocked: This app's request is invalid"

**原因**: OAuth 同意画面の設定が不完足

**対処法**:

1. GCP コンソール → OAuth 同意画面
2. スコープが正しく設定されているか確認
3. テストユーザーに自分のメールアドレスが追加されているか確認

### 認証はできるが、カレンダーが取得できない

**原因**: スコープが不足している

**対処法**:

1. GCP コンソール → OAuth 同意画面 → スコープを編集
2. `https://www.googleapis.com/auth/calendar` を追加
3. n8n でクレデンシャルを削除して再作成

## 次のステップ

Google Calendar API の設定が完了したら、[Gemini API 設定手順](setup-gemini-api.md)に進みましょう。
