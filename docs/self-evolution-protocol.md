# LUMA 自己進化プロトコル v1.0

## 1. 役割分担
- **Architect (Gemini Pro)**: 要件定義、ファイル構成の決定、ステップ分解。
- **Implementer (Qwen3-Coder:30b)**: 具体的なPythonコードの実装、既存コードの修正。
- **Validator (Aider/Interpreter)**: ファイル書き込み、pytestの実行、ログ解析。

## 2. 開発ルール
- **Plugin式拡張**: 新しい機能は `services/fast_service/tools/` ディレクトリに1ファイル1メソッド形式で追加する。
- **Tool登録プロセス**:
    1. `services/fast_service/tools/` に実装ファイルを作成（例: `new_tool.py`）。
    2. `services/fast_service/main.py` で新ツールをインポート。
    3. `main.py` の `SYSTEM_PROMPT` にアクションタグ `[ACTION:NAME:PARAM]` を追記。
    4. `handle_user_message` にアクション検知の `elif` 分岐を追加。
    5. `execute_name_action` 関数を実装し、ツールを呼び出して結果を `send_to_user` する。
- **Test-First**: 機能実装の前に、必ず `services/fast_service/tests/` 配下に `pytest` 用のテストスクリプトを作成する。

## 3. 進化のステップ
1. **Request**: ユーザーからのリクエスト。
2. **Plan**: 必要なアクション名、パラメータ、期待される出力を定義。
3. **Test Draft**: 失敗するテストを作成。
4. **Implementation**: Aiderが `tools/` への実装と `main.py` への統合を同時に行う。
5. **Verification**: `PYTHONPATH=. pytest ...` を実行し、全テスト通過を確認。
