# 🤖 Ultiphoton Solar Power OPC
## Hybrid AI Automation System Guide
### Native FAQs + Meta AI Integration

This guide explains how to set up a powerful hybrid system that uses Facebook's native FAQs for your 15 specific questions, and Meta's AI to handle all other general solar inquiries.

---

## 🌟 Why a Hybrid System?

1. **Native FAQs (The 15 Questions):** These provide exact, pre-approved answers for pricing, locations, and specific products. They appear as clickable buttons in Messenger.
2. **Meta AI (The Backup):** When a customer asks a question that isn't in your 15 FAQs (e.g., "How do solar panels work during a typhoon?"), Meta AI takes over and provides a professional, knowledgeable answer about solar energy.

---

## 🛠️ Phase 1: Set Up Native FAQs (The Foundation)

First, you need to set up the 15 FAQs we created earlier. This ensures your specific business details are always accurate.

1. Go to your Facebook Page **Settings**
2. Navigate to **Messaging** → **Automations**
3. Turn on **Frequently Asked Questions**
4. Add all 15 FAQs from the previous guide
5. Turn on **Instant Reply** (Welcome Message)

*Note: If you haven't done this yet, please refer to the `Facebook_Automations_Complete_Guide.md` provided earlier.*

---

## 🧠 Phase 2: Enable Meta AI for Business

Meta has recently rolled out "AI for Business" directly within the Meta Business Suite. This is the easiest way to add AI without coding.

### Step 1: Access AI Settings
1. Go to **Meta Business Suite** (business.facebook.com)
2. Click on **Settings** (gear icon) in the bottom left
3. Look for **AI for Business** or **Automations** in the menu

### Step 2: Configure the AI Assistant
1. Find the option for **AI Assistant** or **Automated Responses with AI**
2. Toggle it to **ON**
3. You will be asked to define the AI's role and knowledge base.

### Step 3: Train Your Meta AI
Copy and paste this exact prompt into the AI's "Business Description" or "Instructions" field:

```text
You are the official AI assistant for Ultiphoton Solar Power OPC, a leading solar energy provider in the Philippines (Muntinlupa and Batangas). 

Your role is to answer general questions about solar energy, solar panels, inverters, and the benefits of switching to solar power. 

Guidelines:
1. Be helpful, professional, and friendly. Use Taglish (Tagalog-English) naturally.
2. If asked about specific pricing, exact product specs, or locations, tell the user to check the FAQ menu or wait for a human agent.
3. You can explain how solar works, the difference between Grid-Tie and Hybrid systems, benefits of TOPCon/Bifacial panels, and general solar maintenance.
4. Always encourage users to schedule a FREE site inspection with Ultiphoton.
5. Never invent prices or make promises about installation timelines.
```

---

## 💻 Phase 3: Advanced Developer Setup (Optional)

If the native Meta AI for Business feature is not yet available in your region, you can build a custom webhook using the Facebook Developer API.

### What You Need:
1. A Facebook Developer Account
2. A server to host your webhook (e.g., Heroku, Render, or AWS)
3. Python/Node.js knowledge

### The Architecture:
1. **User sends a message** to your page.
2. **Facebook checks** if it matches one of your 15 Native FAQs.
3. If YES → Facebook sends your pre-written FAQ answer.
4. If NO → Facebook sends the message to your **Webhook**.
5. Your Webhook sends the message to an **AI API** (like OpenAI or Meta's Llama).
6. The AI generates a response about solar energy.
7. Your Webhook sends the AI's response back to the user via the **Messenger API**.

### Basic Webhook Code Structure (Python/Flask):

```python
from flask import Flask, request
import requests

app = Flask(__name__)
PAGE_ACCESS_TOKEN = 'YOUR_PAGE_ACCESS_TOKEN'

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        # Webhook verification
        if request.args.get("hub.verify_token") == "YOUR_VERIFY_TOKEN":
            return request.args.get("hub.challenge")
        return "Verification failed", 403
        
    if request.method == 'POST':
        data = request.json
        for entry in data['entry']:
            for messaging_event in entry['messaging']:
                if messaging_event.get('message'):
                    sender_id = messaging_event['sender']['id']
                    message_text = messaging_event['message'].get('text')
                    
                    # 1. Send message to AI API (e.g., Meta Llama or OpenAI)
                    ai_response = get_ai_response(message_text)
                    
                    # 2. Send AI response back to user
                    send_message(sender_id, ai_response)
                    
        return "EVENT_RECEIVED", 200

def get_ai_response(user_message):
    # Call your preferred AI API here
    # Instruct it to act as Ultiphoton's solar expert
    return "This is a placeholder AI response about solar energy."

def send_message(recipient_id, message_text):
    url = f"https://graph.facebook.com/v19.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    requests.post(url, json=payload)

if __name__ == '__main__':
    app.run(port=5000)
```

---

## 🚀 Recommendation for Ultiphoton

For the fastest and most reliable setup:
1. **Start with Phase 1:** Implement the 15 Native FAQs manually using the guide provided earlier. This covers 90% of what customers ask (prices, location, COD).
2. **Check Phase 2:** Look in your Meta Business Suite to see if "AI for Business" is available for your page. If it is, paste the training prompt provided above.
3. **Hold on Phase 3:** Only build a custom developer webhook if you have a dedicated IT person to maintain the server and API keys.

By combining the exact answers of Native FAQs with the general knowledge of Meta AI, you'll have a world-class automated customer service system! ☀️⚡
