import requests
import json
import time

WEBHOOK_URL = "https://discord.com/api/webhooks/1471901257240412224/UIU1zv9dkgY-S1MM6sMCNftN2Z1pX1f943ohAmxLQYk87DLBnyX-r_Pl_cSU1OYJ3tkn"

def send_webhook(data, files=None):
    try:
        if files:
            response = requests.post(WEBHOOK_URL, data=data, files=files)
        else:
            headers = {"Content-Type": "application/json"}
            response = requests.post(WEBHOOK_URL, json=data, headers=headers)
        
        if response.status_code == 204:
            print(f"✅ Success: {data.get('content', 'Embed/File')} (No Content)")
        elif response.status_code == 200:
            print(f"✅ Success: {data.get('content', 'Embed/File')}")
        else:
            print(f"❌ Failed ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def main():
    print("🚀 Starting Webhook Tests...")

    # 1. Simple Text
    print("\n--- Test 1: Simple Text ---")
    send_webhook({"content": "Hello! This is a test message from LUMA."})
    time.sleep(1)

    # 2. Embed Message
    print("\n--- Test 2: Embed Message ---")
    embed_data = {
        "content": "This is a message with an embed.",
        "embeds": [
            {
                "title": "LUMA Verification",
                "description": "Running comprehensive webhook tests.",
                "color": 3447003, # Blue
                "fields": [
                    {"name": "Status", "value": "Testing", "inline": True},
                    {"name": "Verified By", "value": "LUMA-Cycle", "inline": True}
                ],
                "footer": {"text": "Sent via Python Script"}
            }
        ]
    }
    send_webhook(embed_data)
    time.sleep(1)

    # 3. Custom Username & Avatar
    print("\n--- Test 3: Custom Identity ---")
    identity_data = {
        "content": "I am a custom bot identity!",
        "username": "LUMA Test Bot",
        "avatar_url": "https://github.com/google/flax/raw/main/docs/logo.png" # Dummy logo
    }
    send_webhook(identity_data)
    time.sleep(1)

    # 4. TTS Message
    print("\n--- Test 4: TTS Message (Silent check) ---")
    tts_data = {
        "content": "This is a TTS test message.",
        "tts": False 
    }
    send_webhook(tts_data)
    
    print("\n✨ All tests completed.")

if __name__ == "__main__":
    main()
