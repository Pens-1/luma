# LUMA 自己進化プロトコル v1.0

## 1. 役割分担
- **Architect (Gemini Pro)**: 要件定義、ファイル構成の決定、ステップ分解。
- **Implementer (Qwen3-Coder:30b)**: 具体的なPythonコードの実装、既存コードの修正。
- **Validator (Aider/Interpreter)**: ファイル書き込み、pytestの実行、ログ解析。

## 2. 開発ルール
- **Plugin式拡張**: 新しい機能（スクレイピング、計算、通知等）は `backend/app/plugins/` ディレクトリに1ファイル1クラス形式で追加する。
- **Auto-Discovery**: `backend/app/main.py` は `plugins/` 配下のクラスを自動的にFastAPIのRouterとして登録する。
- **Test-First**: 機能実装の前に、必ず期待される入出力を定義したテストスクリプトを作成する。

## 3. 進化のステップ
1. **Request**: ユーザーから「〇〇機能がほしい」というリクエスト。
2. **Plan**: Geminiが `self-evolution-protocol.md` に基づき、必要なプラグイン名とメソッド、入出力スキーマを定義。
3. **Draft**: Qwen3がプラグインファイルを生成。
4. **Integration**: Aiderがファイルを配置し、ホットリロードを確認。
5. **Verification**: 自動テストが実行され、成功すればユーザーに「進化完了」を通知。
