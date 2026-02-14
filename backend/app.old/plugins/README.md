# LUMA Plugin Development Guide (for AI Implementers)

あなたは LUMA の機能を拡張するエンジニア AI です。
新しいプラグインを作成する際は、以下の形式を厳守してください。

## 1. ファイル命名
`plugin_feature_name.py` (スネークケース)

## 2. コード構造
必ず `router` という名前の `APIRouter` インスタンスを作成してください。

```python
from fastapi import APIRouter

router = APIRouter(
    tags=["PluginName"]
)

@router.get("/your-feature")
async def your_feature_endpoint():
    return {"message": "Success"}
```

## 3. 依存関係
新しいライブラリが必要な場合は、コードのコメントに `# pip install library-name` と明記してください。
Validator (Aider) がそれを読み取り、自動でインストールします。

## 4. エラーハンドリング
適切な例外処理を行い、500エラーだけでなく意味のあるエラーメッセージを返してください。
