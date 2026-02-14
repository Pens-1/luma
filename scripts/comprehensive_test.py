import asyncio, httpx, json, os, sys
sys.path.append(os.path.join(os.getcwd(), "backend"))
from app.services.action_handler import execute_actions
from app.bot import ask_ollama

async def simulate(user_input, cid, history):
    print(f"\n--- User: {user_input} ---")
    inp, role, max_t = user_input, "user", 5
    for t in range(max_t):
        print(f"Turn {t+1} Thinking...")
        res = await ask_ollama(cid, inp, role=role)
        print(f"LUMA: {res}")
        out = await execute_actions(res, chat_history=history)
        if out:
            print(f"Action Result: {out[:100]}...")
            inp, role = out, "user"
            history.append({"role": "user", "content": out})
        else:
            print("Final response done.")
            history.append({"role": "assistant", "content": res})
            break

async def run():
    cid, hist = 7777, []
    steps = [
        "こんにちは",
        "今日の天気は？",
        "進行中のタスクは？",
        "「メッセージ」というタスクを追加して",
        "さっき登録したタスクが見つからないよ。判定がおかしいんじゃない？自分で調べてAiderで直して"
    ]
    for s in steps:
        await simulate(s, cid, hist)

if __name__ == "__main__":
    asyncio.run(run())
