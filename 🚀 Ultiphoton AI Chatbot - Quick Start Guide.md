# 🚀 Ultiphoton AI Chatbot - Quick Start Guide

## ⚡ 5-Minute Setup

### What You Have:
- ✅ App ID: `960685283095385`
- ✅ App Secret: `98b1bfb0c80fe91114c804a3f82c8f81`
- ✅ Page Access Token: `EAAXyC6Cg0rwBRPMfQqcrItliXYZAWnhQqmBjhBZCZBYLrTBL8vwY4udFs8WZBlfDZBE1H4erMoZB0qCUvBU9yxhqLGGI1fcdc3rLzZCZBJs8H8iRJAsbwDrpIKM2GnH3Uf6s4gB8LcF8hEucZCvAxw8ifEKFu0p5KbjUV2mGeYe5FRAxge6bHlloofK1G050WyhsHjBaPfQWe2nJZApKtAjKa04krxld7sTPRBF2GD`
- ✅ Page ID: `960685283095385`
- ✅ Verify Token: `ultiphoton_solar_verify_2026`

### What You Need:
- ⏳ OpenAI API Key (get from https://platform.openai.com/)

---

## 🎯 3 Simple Steps

### Step 1: Get OpenAI API Key (2 minutes)
1. Go to https://platform.openai.com/
2. Sign up or log in
3. Go to **API keys**
4. Click **Create new secret key**
5. Copy the key (starts with `sk-`)

### Step 2: Deploy to Render (2 minutes)
1. Go to https://render.com/
2. Sign up with GitHub
3. Click "New +" → "Web Service"
4. Paste the code from `facebook_ai_chatbot.py`
5. Add Environment Variable:
   - **Key:** `OPENAI_API_KEY`
   - **Value:** Your OpenAI key
6. Click Deploy
7. Copy your URL (e.g., `https://ultiphoton-ai-chatbot.onrender.com`)

### Step 3: Connect to Facebook (1 minute)
1. Go to Facebook Developer Console
2. Go to **Messenger** → **Settings**
3. Find **Webhooks**
4. Click **Edit Subscription**
5. Fill in:
   - **Callback URL:** `https://your-url.com/webhook`
   - **Verify Token:** `ultiphoton_solar_verify_2026`
6. Check: `messages`, `messaging_postbacks`
7. Click **Verify and Save**
8. Select your page and **Subscribe**

---

## ✅ Test It!

Send a message to your Facebook page:
- "How do solar panels work?"
- "What's the cost of a 5kW system?"
- "Can I schedule an inspection?"

You should get an AI response in 2-3 seconds! 🤖

---

## 📁 Files You Have:
1. `facebook_ai_chatbot.py` - The main chatbot code
2. `AI_Chatbot_Deployment_Guide.md` - Full setup guide
3. `requirements.txt` - Python dependencies
4. `QUICK_START.md` - This file

---

## 🆘 Need Help?
- Check `AI_Chatbot_Deployment_Guide.md` for detailed instructions
- Check server logs for errors
- Make sure OpenAI API key is valid
- Make sure Webhook URL is correct

---

**Your AI Chatbot is ready to go! 🚀☀️**
