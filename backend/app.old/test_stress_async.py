import asyncio
import sys
import random
sys.path.append("/app")
from app.bot import ask_ollama, chat_histories

async def simulate_channel(channel_id, topic):
    print(f"Starting simulation for Channel {channel_id} (Topic: {topic})")
    for i in range(5):  # 各チャンネル5回ずつ発言
        msg = f"This is message {i} about {topic}. Remember the secret code: {channel_id}-{i}"
        res = await ask_ollama(channel_id, msg)
        print(f"Channel {channel_id} received response.")
        
        # 履歴が10件を超えていないかチェック
        history_len = len(chat_histories.get(channel_id, []))
        if history_len > 11: # システムプロンプト + 10メッセージ
            print(f"❌ ERROR: History bloat in Channel {channel_id}: {history_len}")
        
        # 他のチャンネルの秘密コードが混じっていないかチェック
        for cid, hist in chat_histories.items():
            if cid != channel_id:
                for entry in hist:
                    if f"{channel_id}-" in str(entry):
                        print(f"❌ SECURITY BREACH: Data from {channel_id} leaked to {cid}")

async def main():
    print("🚀 Starting Parallel Context & Long-run Test")
    # 3つのチャンネルで同時に会話
    tasks = [
        simulate_channel(101, "Cooking recipes"),
        simulate_channel(202, "Rust programming"),
        simulate_channel(303, "Space exploration")
    ]
    await asyncio.gather(*tasks)
    print("✅ All channels completed simulation.")

if __name__ == "__main__":
    asyncio.run(main())
