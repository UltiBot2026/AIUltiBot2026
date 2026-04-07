#!/usr/bin/env python3
"""
Ultiphoton Solar Power OPC - AI Chatbot for Facebook Messenger
Powered by OpenAI GPT and Facebook Messenger API
This chatbot answers all queries about solar energy and Ultiphoton's services.
"""

from flask import Flask, request
import requests
import json
import os
from openai import OpenAI

# ==================== CONFIGURATION ====================
app = Flask(__name__)

# Facebook Configuration
PAGE_ACCESS_TOKEN = "EAAXyC6Cg0rwBRMXijCeAV8JjzpkZC5MuvRSbYWKAW3VbEiMuEmyWRNQF8DqGu0jPDRAKxwALL7O8ZBAeR8LqeHo2nFn0GZCkjlzqbFFSOUlxTqQ89sRJvfuZAQbJmFAGMZAHZAkTJyqHwE0z4y6E4OJ8CfKcZAjTZAuy5ZAZBB7LM5dA8wg6OsVOGK4VZC9WX1tZArNwtJJHBuGLDsQ4SlOZAM71XZCwJp02dZCzY4K1qQjqPC5jYxc9vzZCE3IlHJpMV0j6AWZApZAigVR7RYHOK5lZCmFp0EorBHG"
VERIFY_TOKEN = "ultiphoton_solar_verify_2026"
PAGE_ID = "516699488185698"

# OpenAI Configuration
try:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        client = OpenAI(api_key=api_key)
    else:
        print("⚠️ Warning: OPENAI_API_KEY not set")
        client = None
except Exception as e:
    print(f"⚠️ Warning: OpenAI client initialization failed: {e}")
    client = None

# ==================== SYSTEM PROMPT ====================
SYSTEM_PROMPT = """You are the official AI assistant for Ultiphoton Solar Power OPC, a leading solar energy provider in the Philippines.

COMPANY INFORMATION:
- Main Office: Filinvest, Muntinlupa City
- Branch: UltiPhoton Solar Power Batangas
- Service Areas: Batangas City, Laguna, Quezon province, and South Luzon
- Warehouse: Cainta (for bulk orders)

PRODUCTS & SERVICES:
- Solar Panels: Talesun 585W & 620W Bifacial (TOPCon technology)
- Inverters: Deye, Solis, GoodWe, SRNE, Sigenergy
- Mounting & Accessories: SoEasy brand railings, breakers, SPD devices
- Systems: Grid-Tie and Hybrid (with battery) configurations
- Free site inspection available

PRICING RANGES (2026):
- 3kW System: ₱97,500 - ₱120,000
- 5kW System: ₱143,750 - ₱180,000
- 7kW System: ₱194,000 - ₱240,000
- 8kW System: ₱220,500 - ₱270,000
- 10kW System: ₱273,500 - ₱330,000
- 12kW System: ₱323,750 - ₱390,000
- 16kW System: ₱429,000 - ₱520,000

PAYMENT METHODS:
- Bank Transfer (BDO, UnionBank, BPI, EastWest)
- GCash: 0997-369-7123
- NO CASH PAYMENTS
- Installment via credit card coming soon

INSTALLATION:
- Timeline: 1-20 days depending on site conditions
- Free site inspection
- Professional installation team

YOUR ROLE:
1. Answer general questions about solar energy, benefits, how it works
2. Explain the difference between Grid-Tie and Hybrid systems
3. Discuss Bifacial and TOPCon technology
4. Answer questions about maintenance and durability
5. Encourage users to schedule a FREE site inspection
6. Direct specific pricing/product questions to the FAQ menu or human agents
7. Always be friendly, professional, and use natural Taglish (Tagalog-English mix)
8. Never make up prices or promises not mentioned above
9. Always encourage customers to contact for exact quotes

TONE:
- Friendly and professional
- Use emojis occasionally (☀️⚡🏠)
- Respond in Taglish naturally
- Be concise but informative
- Always end with a call-to-action (e.g., "Schedule your free inspection!")
"""

# ==================== WEBHOOK ROUTES ====================

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    """
    Main webhook endpoint for Facebook Messenger
    Handles both verification and incoming messages
    """
    
    if request.method == 'GET':
        # Webhook verification from Facebook
        verify_token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        if verify_token == VERIFY_TOKEN:
            print("✅ Webhook verified successfully!")
            return challenge
        else:
            print("❌ Verification failed - invalid token")
            return "Verification failed", 403
    
    if request.method == 'POST':
        # Process incoming messages
        data = request.json
        
        if data.get('object') == 'page':
            for entry in data.get('entry', []):
                for messaging_event in entry.get('messaging', []):
                    # Check if this is a message event
                    if messaging_event.get('message'):
                        sender_id = messaging_event['sender']['id']
                        message_text = messaging_event['message'].get('text', '')
                        
                        if message_text:
                            print(f"\n📨 Message from {sender_id}: {message_text}")
                            
                            # Get AI response
                            ai_response = get_ai_response(message_text)
                            
                            # Send response back to user
                            send_message(sender_id, ai_response)
                    
                    # Handle quick replies and postbacks
                    if messaging_event.get('postback'):
                        sender_id = messaging_event['sender']['id']
                        payload = messaging_event['postback'].get('payload', '')
                        handle_postback(sender_id, payload)
        
        return "EVENT_RECEIVED", 200

# ==================== AI RESPONSE GENERATION ====================

def get_ai_response(user_message):
    """
    Generate an AI response using OpenAI GPT
    """
    if not client:
        return "Sorry po, may technical issue kami ngayon. Please try again or message us directly. Salamat! 😊"
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        ai_response = response.choices[0].message.content
        print(f"🤖 AI Response: {ai_response}")
        return ai_response
        
    except Exception as e:
        print(f"❌ Error getting AI response: {e}")
        return "Sorry po, may technical issue kami ngayon. Please try again or message us directly. Salamat! 😊"

# ==================== MESSAGE SENDING ====================

def send_message(recipient_id, message_text):
    """
    Send a message back to the user via Facebook Messenger
    """
    url = f"https://graph.facebook.com/v19.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print(f"✅ Message sent to {recipient_id}")
        else:
            print(f"❌ Failed to send message: {response.text}")
    except Exception as e:
        print(f"❌ Error sending message: {e}")

def send_quick_reply(recipient_id, message_text, quick_replies):
    """
    Send a message with quick reply buttons
    """
    url = f"https://graph.facebook.com/v19.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    
    payload = {
        "recipient": {"id": recipient_id},
        "message": {
            "text": message_text,
            "quick_replies": quick_replies
        }
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print(f"✅ Quick reply sent to {recipient_id}")
        else:
            print(f"❌ Failed to send quick reply: {response.text}")
    except Exception as e:
        print(f"❌ Error sending quick reply: {e}")

# ==================== POSTBACK HANDLING ====================

def handle_postback(sender_id, payload):
    """
    Handle postback events from quick replies and buttons
    """
    print(f"📌 Postback from {sender_id}: {payload}")
    
    if payload == "SCHEDULE_INSPECTION":
        send_message(sender_id, 
            "Great! Para ma-schedule ang free site inspection, pwede po ba naming malaman:\n"
            "1. Your name po?\n"
            "2. Your address?\n"
            "3. Your contact number?\n\n"
            "Ise-send po namin ang details sa team natin para ma-coordinate ang inspection. Salamat! 😊")
    
    elif payload == "LEARN_MORE":
        send_message(sender_id,
            "Interested ka na sa solar? Eto po ang benefits:\n"
            "☀️ Lower electricity bills (up to 80% savings)\n"
            "⚡ 25+ years of energy production\n"
            "🌍 Eco-friendly and sustainable\n"
            "🏠 Increase home value\n\n"
            "Ready na ba para sa free site inspection? 😊")
    
    elif payload == "CONTACT_US":
        send_message(sender_id,
            "📞 Contact Ultiphoton Solar Power OPC:\n\n"
            "🏢 Main Office: Filinvest, Muntinlupa City\n"
            "🏢 Branch: Batangas\n"
            "📱 GCash: 0997-369-7123\n\n"
            "May iba pang tanong po ba? 😊")

# ==================== WELCOME MESSAGE ====================

@app.route('/send_welcome', methods=['POST'])
def send_welcome():
    """
    Send a welcome message to a specific user (for testing)
    """
    data = request.json
    recipient_id = data.get('recipient_id')
    
    welcome_message = (
        "Hello po! 👋 Salamat sa pag-message sa Ultiphoton Solar Power OPC.\n\n"
        "I'm your AI assistant, ready to answer any questions about solar energy! ☀️⚡\n\n"
        "What would you like to know?"
    )
    
    send_message(recipient_id, welcome_message)
    return {"status": "Welcome message sent"}, 200

# ==================== HEALTH CHECK ====================

@app.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint
    """
    return {"status": "OK", "service": "Ultiphoton AI Chatbot"}, 200

# ==================== MAIN ====================

if __name__ == '__main__':
    print("🚀 Starting Ultiphoton AI Chatbot Server...")
    print(f"📍 Page ID: {PAGE_ID}")
    print(f"🔐 Verify Token: {VERIFY_TOKEN}")
    print("⏳ Listening for messages...\n")
    
    # Run on port 5000 (Render will use PORT env variable)
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
