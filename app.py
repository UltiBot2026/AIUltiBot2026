"""
Ultiphoton Solar Power OPC - AI Chatbot for Facebook Messenger
FAQ-Aware AI System with Specific Company Information & Pricing
"""

from flask import Flask, request
import requests
import json
import os
import sys
import time
import re

app = Flask(__name__)

# Configuration
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN", "").strip()
if not PAGE_ACCESS_TOKEN:
    PAGE_ACCESS_TOKEN = "default_token_here"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
PAGE_ID = "516699488185698"
VERIFY_TOKEN = "ultiphoton_solar_verify_2026"

print("\n" + "="*70)
print("🤖 ULTIPHOTON SOLAR POWER OPC - AI CHATBOT (FAQ-AWARE)")
print("="*70)
print(f"✅ Page ID: {PAGE_ID}")
print(f"✅ Access Token: {'✓ SET' if PAGE_ACCESS_TOKEN else '✗ NOT SET'}")
print(f"✅ OpenAI Key: {'✓ SET' if OPENAI_API_KEY else '✗ NOT SET'}")
print("="*70 + "\n")
sys.stdout.flush()

# FAQ Database with Updated Information
FAQS = {
    "solar_panel_price": {
        "keywords": ["magkano", "price", "cost", "solar panel", "talesun", "585w", "620w", "how much"],
        "answer": """☀️ **Solar Panel Pricing:**

**Talesun 585W Bifacial** ✅ (Available)
- ₱5,750/pc (9 pieces or less)
- ₱5,650/pc (10 pieces or more - Installer price)

**Talesun 620W** ❌ (Out of stock in Batangas)
- Available for pick-up at **Cainta Warehouse** ✅

Contact us for bulk orders and special pricing! 📞"""
    },
    
    "location": {
        "keywords": ["location", "located", "saan", "address", "office", "branch", "where"],
        "answer": """📍 **Our Locations:**

**Main Office:**
Filinvest, Muntilupa City
[Google Map: UltiPhoton Solar Power OPC]

**Branch:**
UltiPhoton Solar Power Batangas
[Google Map: UltiPhoton Solar Power Batangas]

Feel free to visit us! ☀️"""
    },
    
    "cod": {
        "keywords": ["cod", "delivery", "cash on delivery", "available", "area", "deliver"],
        "answer": """✅ **Cash on Delivery Available!**

We offer COD within **Batangas City area**.

We can also deliver to:
• Laguna
• Quezon Province
• Whole South Luzon

Contact us for delivery details! 🚚"""
    },
    
    "panel_specs": {
        "keywords": ["talesun", "panel", "dimension", "size", "specs", "specifications", "sukat"],
        "answer": """📋 **Talesun Solar Panel Specifications:**

**Talesun 585W Bifacial:**
- High efficiency bifacial technology
- Optimized for Philippine climate
- [Check Talesun spec sheet for dimensions]

**Talesun 620W Bifacial:**
- Premium bifacial technology
- [Check Talesun spec sheet for dimensions]

For detailed specifications, please visit Talesun's official website or contact us! 📞"""
    },
    
    "payment": {
        "keywords": ["payment", "pay", "bank", "transfer", "cash", "gcash", "paano", "bayad"],
        "answer": """💳 **Payment Methods:**

We accept **Bank Transfer ONLY** (No cash payments)

**Bank Details:**

**BDO:**
Account Name: JERWIN JEFFREY GAPUZ
Savings Account: 0081 9600 1660

**UnionBank:**
Account Name: JERWIN JEFFREY GAPUZ
Savings Account: 1094 2921 2487

**BPI:**
Account Name: JERWIN JEFFREY GAPUZ
Savings Account: 065 6925 517

**EastWest:**
Account: 200064679316

**GCash:**
0997-369-7123 (J. GAPUZ)

Please transfer and provide proof of payment! 🏦"""
    },
    
    "accessories": {
        "keywords": ["railing", "mounting", "accessories", "breaker", "wire", "protection", "device", "meron"],
        "answer": """🔧 **Available Accessories & Mounting:**

**Solar Mounting (SoEasy Brand):**
- 2.4m Railing: ₱600/pc
- L-ft: ₱90/pc
- Mid: ₱85/pc
- End: ₱85/pc

**AC & DC Breakers (Chint Brand):**
- AC Breaker: ₱600-₱1,000/pc (depends on Ampere Trip)
- DC Breaker: ₱700/pc
- DC SPD: ₱845/pc

Quality protection for your inverter and battery! ⚡"""
    },
    
    "warehouse": {
        "keywords": ["warehouse", "cainta", "batangas", "paleta", "minimum order", "lang ba"],
        "answer": """🏭 **Warehouse Information:**

We have a **Cainta Warehouse** ✅

**Minimum Order:**
1 pallet for 625W and 585W solar panels

We serve beyond Batangas area through our warehouse! 📦

Contact us for bulk orders! 📞"""
    },
    
    "inverter_brands": {
        "keywords": ["inverter", "brand", "deye", "solis", "goodwe", "srne", "sigenergy", "ano mga"],
        "answer": """⚡ **Inverter Brands Available:**

✅ **Deye** - 5 years warranty
✅ **Solis** - 5 years warranty
✅ **GoodWe** - 5 years warranty
✅ **SRNE** - 5 years warranty
✅ **Sigenergy** - 10 years warranty

All brands are high-quality and reliable for Philippine climate! 🌞"""
    },
    
    "warranty": {
        "keywords": ["warranty", "years", "guarantee", "coverage", "ilang"],
        "answer": """✅ **Warranty Coverage:**

**Solar Panels (Talesun):**
10 years warranty

**Inverters:**
- Deye, Solis, SRNE, GoodWe: 5 years
- Sigenergy: 10 years

Quality guaranteed! ☀️"""
    },
    
    "inverter_price": {
        "keywords": ["inverter price", "cost", "how much", "inverter", "price"],
        "answer": """💰 **Inverter Pricing:**

Prices vary by brand and capacity:
- **Deye, Solis, GoodWe, SRNE:** Budget-friendly options
- **Sigenergy:** Premium options

For specific pricing, please contact us for a quotation! 📞

We provide competitive Philippine market prices! 💵"""
    },
    
    "package_quote": {
        "keywords": ["quote", "3kw", "5kw", "7kw", "8kw", "10kw", "12kw", "16kw", "package", "system", "pwede pa"],
        "answer": """📊 **Solar Package Quotes Available:**

We offer complete systems for:
✅ 3kW Single Phase
✅ 5kW Single Phase
✅ 7kW Single Phase
✅ 8kW Single Phase
✅ 10kW Single Phase
✅ 12kW Single Phase
✅ 16kW Single Phase

**Each package includes:**
- Talesun Solar Panels
- Quality Inverter (Deye/Solis/GoodWe/SRNE/Sigenergy)
- Mounting & Accessories
- Installation & Support

**Request a customized quote now!** Contact us for competitive pricing! 📞"""
    },
    
    "battery": {
        "keywords": ["battery", "storage", "backup", "energy storage", "may battery"],
        "answer": """🔋 **Battery Storage:**

Yes, we offer batteries **by order only**

We don't keep batteries in stock, but we can source them for you based on your requirements.

Contact us to discuss your battery needs! 📞"""
    },
    
    "installment": {
        "keywords": ["installment", "instalment", "payment plan", "credit card", "visa", "mastercard", "may instalment"],
        "answer": """💳 **Installment Payment:**

**Currently:** Cash basis only

**Coming Soon:** Credit Card Installment
- Visa
- MasterCard
- JCB

Stay tuned for installment options! 🎯"""
    },
    
    "installation_time": {
        "keywords": ["installation", "how long", "days", "time", "duration", "gaano katagal"],
        "answer": """⏱️ **Installation Timeline:**

**Duration:** 1 day to 20 days

**Depends on:**
- Site conditions
- System complexity
- Weather conditions

We'll provide a specific timeline after site inspection! 🏗️"""
    },
    
    "site_inspection": {
        "keywords": ["site inspection", "libre", "free", "survey", "inspect"],
        "answer": """🔍 **Site Inspection:**

✅ **FREE Site Inspection!**

We provide complimentary site inspection to assess your property and design the perfect solar system for you.

**Condition:** We hope you'll choose us for installation! 😊

Schedule your free inspection today! 📞"""
    }
}

def find_matching_faq(user_message):
    """Find matching FAQ based on user message keywords"""
    message_lower = user_message.lower()
    
    for faq_key, faq_data in FAQS.items():
        for keyword in faq_data["keywords"]:
            if keyword.lower() in message_lower:
                return faq_data["answer"]
    
    return None

def get_ai_response(user_message):
    """Get AI response from OpenAI with FAQ context"""
    try:
        print(f"🤖 Processing: {user_message[:50]}...")
        sys.stdout.flush()
        
        # Check for FAQ match first
        faq_answer = find_matching_faq(user_message)
        if faq_answer:
            print(f"✅ FAQ Match Found!")
            sys.stdout.flush()
            return faq_answer
        
        # If no FAQ match, use AI to generate response
        print(f"🤖 Using AI to generate response...")
        sys.stdout.flush()
        
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        faq_context = "\n".join([f"- {key}: {data['keywords']}" for key, data in FAQS.items()])
        
        payload = {
            "model": "gpt-4.1-mini",
            "messages": [
                {
                    "role": "system",
                    "content": f"""You are a helpful AI assistant for Ultiphoton Solar Power OPC, a solar panel company in the Philippines.

Company Information:
- Main Office: Filinvest, Muntilupa City
- Branch: Batangas
- Warehouse: Cainta
- Products: Talesun Solar Panels (585W ₱5,750/pc, 620W available), Inverters (Deye, Solis, GoodWe, SRNE, Sigenergy)
- Services: Installation, Maintenance, Consultation
- Delivery: COD available in Batangas, Laguna, Quezon, South Luzon

Available FAQ Topics: {faq_context}

Guidelines:
1. Be friendly, professional, and helpful
2. Answer in both English and Filipino (Tagalog) when appropriate
3. Keep responses concise (under 100 words)
4. If you don't know specific details, suggest they contact the company
5. Always mention "Feel free to contact us!" at the end
6. Use emojis to make responses friendly ☀️⚡💚
7. For pricing questions, refer to FAQ or suggest contacting for quote"""
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
            timeout=15
        )
        
        if response.status_code == 200:
            ai_response = response.json()["choices"][0]["message"]["content"].strip()
            print(f"✅ AI Response: {ai_response[:80]}...")
            sys.stdout.flush()
            return ai_response
        else:
            print(f"❌ OpenAI Error: {response.status_code}")
            sys.stdout.flush()
            return "Sorry, I'm having trouble processing your request. Please try again or contact us directly! 📞"
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.stdout.flush()
        return "Sorry, I encountered an error. Please contact us directly! 📞"

def send_message(recipient_id, message_text):
    """Send message via Facebook Messenger API"""
    try:
        print(f"📤 Sending to {recipient_id}...")
        sys.stdout.flush()
        
        url = f"https://graph.facebook.com/v19.0/{PAGE_ID}/messages"
        
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": message_text}
        }
        
        params = {
            "access_token": PAGE_ACCESS_TOKEN
        }
        
        print(f"   Token length: {len(PAGE_ACCESS_TOKEN)} chars")
        print(f"   URL: {url}")
        print(f"   Payload keys: {list(payload.keys())}")
        sys.stdout.flush()
        
        response = requests.post(url, json=payload, params=params, timeout=10)
        
        print(f"   Status: {response.status_code}")
        sys.stdout.flush()
        
        if response.status_code == 200:
            print(f"✅ Message sent successfully!")
            sys.stdout.flush()
            return True
        else:
            print(f"❌ Facebook Error: {response.status_code}")
            print(f"   Response: {json.dumps(response.json(), indent=2)}")
            sys.stdout.flush()
            return False
            
    except Exception as e:
        print(f"❌ Error sending message: {str(e)}")
        sys.stdout.flush()
        return False

@app.route("/", methods=["GET"])
def home():
    return "🤖 Ultiphoton Solar Power OPC Chatbot is running!", 200

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        verify_token = request.args.get("verify_token")
        challenge = request.args.get("challenge")
        
        if verify_token == VERIFY_TOKEN:
            return challenge
        return "Invalid token", 403
    
    elif request.method == "POST":
        try:
            data = request.get_json()
            
            if data.get("object") == "page":
                for entry in data.get("entry", []):
                    for messaging in entry.get("messaging", []):
                        sender_id = messaging.get("sender", {}).get("id")
                        message = messaging.get("message", {}).get("text")
                        
                        if sender_id and message:
                            print(f"\n📨 Message from {sender_id}: {message}")
                            sys.stdout.flush()
                            
                            # Get AI response (with FAQ checking)
                            response_text = get_ai_response(message)
                            
                            # Send response
                            if response_text:
                                send_message(sender_id, response_text)
            
            return "EVENT_RECEIVED", 200
            
        except Exception as e:
            print(f"❌ Webhook Error: {str(e)}")
            sys.stdout.flush()
            return "ERROR", 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
