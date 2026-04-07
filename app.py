"""
Ultiphoton Solar Power OPC - AI Chatbot for Facebook Messenger
Ultra-simplified version with direct HTTP requests to OpenAI
"""

from flask import Flask, request
import requests
import json
import os
import sys

app = Flask(__name__)

# Configuration - Read from environment variables
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
PAGE_ID = "516699488185698"
VERIFY_TOKEN = "ultiphoton_solar_verify_2026"

# Startup logging
print("\n" + "="*70)
print("🤖 ULTIPHOTON SOLAR POWER OPC - AI CHATBOT")
print("="*70)
print(f"✅ Page ID: {PAGE_ID}")
print(f"✅ Access Token: {'✓ SET' if PAGE_ACCESS_TOKEN else '✗ NOT SET'} ({len(PAGE_ACCESS_TOKEN)} chars)")
print(f"✅ OpenAI Key: {'✓ SET' if OPENAI_API_KEY else '✗ NOT SET'} ({len(OPENAI_API_KEY)} chars)")
print("="*70 + "\n")

sys.stdout.flush()


def get_ai_response(user_message):
    """Get AI response from OpenAI using direct HTTP requests"""
    try:
        print(f"🤖 Processing: {user_message[:50]}...")
        sys.stdout.flush()
        
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4.1-mini",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful AI assistant for Ultiphoton Solar Power OPC. Answer questions about solar panels and solar energy. Be friendly, professional, and concise (under 100 words). If unsure, suggest contacting Ultiphoton directly."
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            "temperature": 0.7,
            "max_tokens": 150
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_message = result["choices"][0]["message"]["content"].strip()
            print(f"✅ AI Response: {ai_message[:50]}...")
            sys.stdout.flush()
            return ai_message
        else:
            error_msg = f"OpenAI Error {response.status_code}"
            print(f"❌ {error_msg}")
            print(f"   Response: {response.text[:200]}")
            sys.stdout.flush()
            return "Sorry, I'm having trouble processing your request. Please try again."
            
    except Exception as e:
        print(f"❌ Error in get_ai_response: {str(e)}")
        sys.stdout.flush()
        return "Sorry, I encountered an error. Please try again later."


def send_message(recipient_id, message_text):
    """Send message to user via Facebook Messenger API"""
    try:
        print(f"📤 Sending to {recipient_id}...")
        print(f"   Token length: {len(PAGE_ACCESS_TOKEN)} chars")
        sys.stdout.flush()
        
        url = f"https://graph.facebook.com/v19.0/{PAGE_ID}/messages"
        
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": message_text}
        }
        
        params = {"access_token": PAGE_ACCESS_TOKEN}
        
        response = requests.post(
            url,
            json=payload,
            params=params,
            timeout=15
        )
        
        if response.status_code == 200:
            print(f"✅ Message sent successfully!")
            sys.stdout.flush()
            return True
        else:
            print(f"❌ Facebook Error: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            sys.stdout.flush()
            return False
            
    except Exception as e:
        print(f"❌ Send Error: {str(e)}")
        sys.stdout.flush()
        return False


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    """Facebook Webhook endpoint"""
    
    if request.method == "GET":
        verify_token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        
        if verify_token == VERIFY_TOKEN:
            print("✅ Webhook verified!")
            sys.stdout.flush()
            return challenge
        else:
            print(f"❌ Verification failed")
            sys.stdout.flush()
            return "Unauthorized", 403
    
    elif request.method == "POST":
        data = request.get_json()
        
        if data.get("object") == "page":
            for entry in data.get("entry", []):
                for messaging_event in entry.get("messaging", []):
                    sender_id = messaging_event.get("sender", {}).get("id")
                    message_data = messaging_event.get("message", {})
                    message_text = message_data.get("text", "").strip()
                    
                    if sender_id and message_text:
                        print(f"\n📨 Message from {sender_id}: {message_text}")
                        sys.stdout.flush()
                        
                        # Get AI response
                        ai_response = get_ai_response(message_text)
                        
                        # Send response
                        success = send_message(sender_id, ai_response)
                        
                        if success:
                            print(f"✅ Response delivered!")
                        else:
                            print(f"❌ Failed to deliver response")
                        sys.stdout.flush()
        
        return "EVENT_RECEIVED", 200


@app.route("/", methods=["GET"])
def index():
    """Health check"""
    return {"status": "ok", "service": "Ultiphoton AI Chatbot"}, 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    print(f"🚀 Starting server on port {port}...\n")
    sys.stdout.flush()
    app.run(host="0.0.0.0", port=port, debug=False)
