#!/usr/bin/env python3
"""
Ultra-simplified Ultiphoton Solar Power OPC - AI Chatbot for Facebook Messenger
Powered by OpenAI GPT and Facebook Messenger API
No problematic library dependencies - uses only requests and flask
"""

from flask import Flask, request
import requests
import json
import os

app = Flask(__name__)

# Configuration from environment variables
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
PAGE_ID = "516699488185698"
VERIFY_TOKEN = "ultiphoton_solar_verify_2026"

print("=" * 60)
print("🤖 Ultiphoton Solar Power OPC - AI Chatbot")
print("=" * 60)
print(f"✅ PAGE_ID: {PAGE_ID}")
print(f"✅ PAGE_ACCESS_TOKEN: {'Set' if PAGE_ACCESS_TOKEN else 'NOT SET'}")
print(f"✅ OPENAI_API_KEY: {'Set' if OPENAI_API_KEY else 'NOT SET'}")
print("=" * 60)


def get_ai_response(user_message):
    """
    Get AI response from OpenAI API using HTTP requests
    """
    try:
        print(f"🤖 Generating AI response for: {user_message}")
        
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4.1-mini",
            "messages": [
                {
                    "role": "system",
                    "content": """You are a helpful AI assistant for Ultiphoton Solar Power OPC, a company that sells solar panels and solar energy solutions. 
                    
You should:
- Answer questions about solar panels, solar energy, and Ultiphoton's services
- Be friendly and professional
- Keep responses concise (under 150 words)
- If you don't know something, suggest contacting Ultiphoton directly
- Always be enthusiastic about renewable energy!

Ultiphoton Solar Power OPC specializes in:
- High-quality solar panels
- Solar installation services
- Solar energy consulting
- Maintenance and support"""
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            "temperature": 0.7,
            "max_tokens": 200
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        print(f"📊 OpenAI Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            ai_message = result["choices"][0]["message"]["content"]
            print(f"✅ AI Response: {ai_message}")
            return ai_message
        else:
            print(f"❌ OpenAI Error: {response.text}")
            return "Sorry, I'm having trouble processing your request. Please try again later."
            
    except Exception as e:
        print(f"❌ Error getting AI response: {e}")
        return "Sorry, I encountered an error. Please try again later."


def send_message(recipient_id, message_text):
    """
    Send a message to a user via Facebook Messenger API
    """
    try:
        print(f"📤 Sending message to {recipient_id}: {message_text}")
        
        url = f"https://graph.facebook.com/v19.0/{PAGE_ID}/messages"
        
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": message_text}
        }
        
        params = {
            "access_token": PAGE_ACCESS_TOKEN
        }
        
        response = requests.post(
            url,
            json=payload,
            params=params,
            timeout=10
        )
        
        print(f"📊 Facebook API Response Status: {response.status_code}")
        print(f"📝 Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Message sent! ID: {result.get('message_id')}")
            return True
        else:
            print(f"❌ Failed to send message: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    """
    Facebook Webhook endpoint
    """
    if request.method == "GET":
        # Webhook verification
        verify_token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        
        if verify_token == VERIFY_TOKEN:
            print("✅ Webhook verified!")
            return challenge
        else:
            print(f"❌ Webhook verification failed! Token: {verify_token}")
            return "Unauthorized", 403
    
    elif request.method == "POST":
        # Handle incoming messages
        data = request.get_json()
        
        if data["object"] == "page":
            for entry in data.get("entry", []):
                for messaging_event in entry.get("messaging", []):
                    sender_id = messaging_event["sender"]["id"]
                    
                    if messaging_event.get("message"):
                        message_text = messaging_event["message"].get("text", "")
                        
                        if message_text:
                            print(f"\n📨 Message from {sender_id}: {message_text}")
                            
                            # Get AI response
                            ai_response = get_ai_response(message_text)
                            
                            # Send response back to user
                            send_message(sender_id, ai_response)
        
        return "EVENT_RECEIVED", 200


@app.route("/", methods=["GET"])
def index():
    """
    Health check endpoint
    """
    return {"status": "ok", "message": "Ultiphoton AI Chatbot is running!"}, 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
