import random

async def play_janken(user_hand: str) -> dict:
    """
    じゃんけんを行うツール
    Args:
        user_hand (str): ユーザーの手 (グー, チョキ, パー)
    Returns:
        dict: 前回の結果
    """
    hands = ["グー", "チョキ", "パー"]
    
    # 正規化
    user_hand = user_hand.strip()
    if user_hand not in hands:
        # 簡易的なマッピング
        mapping = {
            "rock": "グー", "sissors": "チョキ", "scissors": "チョキ", "paper": "パー",
            "gu": "グー", "choki": "チョキ", "pa": "パー"
        }
        user_hand = mapping.get(user_hand.lower(), user_hand)
    
    if user_hand not in hands:
        return {"error": f"無効な手です。{hands} のいずれかを指定してください。", "status": "error"}

    computer_hand = random.choice(hands)
    
    result = "draw"
    message = "引き分けです！"
    
    if user_hand == computer_hand:
        result = "draw"
        message = "引き分けです！"
    elif (user_hand == "グー" and computer_hand == "チョキ") or \
         (user_hand == "チョキ" and computer_hand == "パー") or \
         (user_hand == "パー" and computer_hand == "グー"):
        result = "win"
        message = "あなたの勝ちです！🎉"
    else:
        result = "lose"
        message = "コンピュータの勝ちです...🤖"

    return {
        "user_hand": user_hand,
        "computer_hand": computer_hand,
        "result": result,
        "message": message
    }
