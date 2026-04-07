"""
Ultiphoton Solar Power OPC - Advanced AI Chatbot for Facebook Messenger
Features: Language Detection, Conversation Memory, Typing Indicator, Quick Replies, 
Analytics, Auto-Greeting, Business Hours Response
"""

from flask import Flask, request
import requests
import json
import os
import sys
import time
import re
from datetime import datetime
from collections import defaultdict
import sqlite3
from threading import Lock

app = Flask(__name__)

# Configuration
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN", "").strip()
if not PAGE_ACCESS_TOKEN:
    PAGE_ACCESS_TOKEN = "default_token_here"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
PAGE_ID = "516699488185698"
VERIFY_TOKEN = "ultiphoton_solar_verify_2026"

# Business Hours (Philippine Time - PST/PHT)
BUSINESS_HOURS = {
    "start": 8,      # 8 AM
    "end": 18,       # 6 PM
    "days": [0, 1, 2, 3, 4, 5, 6]  # All days (0=Monday, 6=Sunday)
}

# Database lock for thread safety
db_lock = Lock()

print("\n" + "="*70)
print("🤖 ULTIPHOTON SOLAR POWER OPC - ADVANCED AI CHATBOT")
print("="*70)
print(f"✅ Page ID: {PAGE_ID}")
print(f"✅ Access Token: {'✓ SET' if PAGE_ACCESS_TOKEN else '✗ NOT SET'}")
print(f"✅ OpenAI Key: {'✓ SET' if OPENAI_API_KEY else '✗ NOT SET'}")
print("✅ Features: Language Detection | Conversation Memory | Typing Indicator")
print("✅ Features: Quick Replies | Analytics | Auto-Greeting | Business Hours")
print("="*70 + "\n")
sys.stdout.flush()

# Initialize Database
def init_database():
    """Initialize SQLite database for conversation history and analytics"""
    try:
        with db_lock:
            conn = sqlite3.connect('/tmp/ultiphoton_chatbot.db')
            cursor = conn.cursor()
            
            # Conversation history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    message TEXT NOT NULL,
                    response TEXT NOT NULL,
                    language TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    faq_matched BOOLEAN DEFAULT 0
                )
            ''')
            
            # Analytics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    faq_key TEXT,
                    keyword TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # User preferences table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id TEXT PRIMARY KEY,
                    language TEXT DEFAULT 'auto',
                    first_message_sent BOOLEAN DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            print("✅ Database initialized successfully")
            sys.stdout.flush()
    except Exception as e:
        print(f"❌ Database init error: {str(e)}")
        sys.stdout.flush()

init_database()

# ─── Excel Price Loader ───────────────────────────────────────────────────────
import os as _os

EXCEL_PATH = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "pricelist.xlsx")

def load_prices_from_excel():
    """
    Read pricelist.xlsx and return a dict:
      {
        'solar_panels': [{'item': ..., 'price': ..., 'installer_price': ...}, ...],
        'pv_mountings': [{'item': ..., 'brand': ..., 'price': ...}, ...],
        'dc_breakers':  [...],
        'ac_breakers':  [...],
        'spd':          [...],
        'mc4':          [...],
        'battery_breaker': [...],
      }
    Returns empty dict on any error.
    """
    try:
        import openpyxl
        wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
        data = {}

        # --- Solar Panels ---
        ws = wb["SOLAR PANEL"]
        panels = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            item, brand, _, price, installer = (row + (None,)*5)[:5]
            if item and price:
                item_clean = str(item).replace("\n", " ").strip()
                price_clean = str(price).replace("P", "₱").strip()
                inst_clean  = str(installer).replace("P", "₱").strip() if installer else None
                panels.append({"item": item_clean, "brand": brand, "price": price_clean, "installer_price": inst_clean})
        data["solar_panels"] = panels

        # --- PV Mountings ---
        ws = wb["PV MOUNTINGS"]
        mountings = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            item, brand, _, price = (row + (None,)*4)[:4]
            if item and price is not None:
                mountings.append({"item": str(item).strip(), "brand": brand, "price": f"₱{int(price):,}"})
        data["pv_mountings"] = mountings

        # --- DC Breakers ---
        ws = wb["DC BREAKERS"]
        dc = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            item, brand, _, price = (row + (None,)*4)[:4]
            if item and price is not None:
                dc.append({"item": str(item).strip(), "brand": brand, "price": f"₱{int(price):,}"})
        data["dc_breakers"] = dc

        # --- AC Breakers ---
        ws = wb["AC BREAKERS"]
        ac = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            item, brand, _, price = (row + (None,)*4)[:4]
            if item and price is not None:
                ac.append({"item": str(item).strip(), "brand": brand, "price": f"₱{int(price):,}"})
        data["ac_breakers"] = ac

        # --- SPD ---
        ws = wb["AC & DC SPD"]
        spd = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            item, brand, _, price = (row + (None,)*4)[:4]
            if item and price is not None:
                spd.append({"item": str(item).strip(), "brand": brand, "price": f"₱{int(price):,}"})
        data["spd"] = spd

        # --- MC4 ---
        ws = wb["MC4"]
        mc4 = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            item, brand, _, price = (row + (None,)*4)[:4]
            if item and price is not None:
                mc4.append({"item": str(item).strip(), "brand": brand, "price": f"₱{int(price):,}"})
        data["mc4"] = mc4

        # --- Battery Breaker ---
        ws = wb["BATTERY BREAKER"]
        bb = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            item, brand, _, price = (row + (None,)*4)[:4]
            if item and price is not None:
                bb.append({"item": str(item).strip(), "brand": brand, "price": f"₱{int(price):,}"})
        data["battery_breaker"] = bb

        print(f"✅ Price list loaded from Excel: {sum(len(v) for v in data.values())} items")
        sys.stdout.flush()
        return data
    except Exception as e:
        print(f"⚠️  Could not load Excel price list: {e}")
        sys.stdout.flush()
        return {}


def build_pricelist_answer(lang="en"):
    """Build a formatted price list message from the Excel data."""
    prices = load_prices_from_excel()
    if not prices:
        # Fallback to hardcoded if Excel unavailable
        return None

    lines = []
    if lang == "tl":
        lines.append("💰 *Opisyal na Listahan ng Presyo ng Ultiphoton:*")
    else:
        lines.append("💰 *Ultiphoton Official Price List:*")

    # Solar Panels
    if prices.get("solar_panels"):
        lines.append("\n☀️ *Solar Panels (Talesun):*")
        for p in prices["solar_panels"]:
            line = f"- {p['item']}: {p['price']}"
            if p.get("installer_price"):
                line += f" / {p['installer_price']} (installer)"
            lines.append(line)

    # PV Mountings
    if prices.get("pv_mountings"):
        lines.append("\n📌 *PV Mountings (SoEasy):*")
        for p in prices["pv_mountings"]:
            lines.append(f"- {p['item']}: {p['price']}")

    # DC Breakers
    if prices.get("dc_breakers"):
        lines.append("\n📌 *DC Breakers (Chint/Chyt):*")
        for p in prices["dc_breakers"]:
            lines.append(f"- {p['item']}: {p['price']}")

    # AC Breakers
    if prices.get("ac_breakers"):
        lines.append("\n📌 *AC Breakers (Chint/Chyt):*")
        for p in prices["ac_breakers"]:
            lines.append(f"- {p['item']}: {p['price']}")

    # SPD
    if prices.get("spd"):
        lines.append("\n📌 *Surge Protection (SPD):*")
        for p in prices["spd"]:
            lines.append(f"- {p['item']}: {p['price']}")

    # MC4
    if prices.get("mc4"):
        lines.append("\n📌 *Connectors:*")
        for p in prices["mc4"]:
            lines.append(f"- {p['item']}: {p['price']}")

    # Battery Breaker
    if prices.get("battery_breaker"):
        lines.append("\n📌 *Battery Breaker:*")
        for p in prices["battery_breaker"]:
            lines.append(f"- {p['item']}: {p['price']}")

    if lang == "tl":
        lines.append("\nMakipag-ugnayan para sa bulk orders at inverter pricing! 📞")
    else:
        lines.append("\nContact us for bulk orders & inverter pricing! 📞")

    return "\n".join(lines)


def build_solar_panel_answer(lang="en"):
    """Build solar panel pricing answer from Excel."""
    prices = load_prices_from_excel()
    panels = prices.get("solar_panels", [])
    if not panels:
        return None

    lines = []
    if lang == "tl":
        lines.append("☀️ *Presyo ng Solar Panels (Talesun):*")
    else:
        lines.append("☀️ *Solar Panel Pricing (Talesun):*")

    for p in panels:
        lines.append(f"\n*{p['item']}*")
        lines.append(f"- Retail: {p['price']}")
        if p.get("installer_price"):
            lines.append(f"- Installer: {p['installer_price']}")

    if lang == "tl":
        lines.append("\nMakipag-ugnayan sa amin para sa bulk orders! 📞")
    else:
        lines.append("\nContact us for bulk orders and special pricing! 📞")

    return "\n".join(lines)


def build_accessories_answer(lang="en"):
    """Build accessories/materials pricing answer from Excel."""
    prices = load_prices_from_excel()
    sections = [
        ("pv_mountings",    "📌 *PV Mountings (SoEasy):*"),
        ("dc_breakers",     "📌 *DC Breakers (Chint/Chyt):*"),
        ("ac_breakers",     "📌 *AC Breakers (Chint/Chyt):*"),
        ("spd",             "📌 *Surge Protection (SPD):*"),
        ("mc4",             "📌 *Connectors:*"),
        ("battery_breaker", "📌 *Battery Breaker:*"),
    ]
    if not any(prices.get(k) for k, _ in sections):
        return None

    lines = []
    if lang == "tl":
        lines.append("🔧 *Listahan ng Presyo ng Accessories & Materials:*")
    else:
        lines.append("🔧 *Accessories & Materials Price List:*")

    for key, header in sections:
        items = prices.get(key, [])
        if items:
            lines.append(f"\n{header}")
            for p in items:
                lines.append(f"- {p['item']}: {p['price']}")

    if lang == "tl":
        lines.append("\nMakipag-ugnayan para sa bulk orders! ⚡")
    else:
        lines.append("\nContact us for bulk orders! ⚡")

    return "\n".join(lines)

# ─────────────────────────────────────────────────────────────────────────────

# FAQ Database with Updated Information
FAQS = {
    "solar_panel_price": {
        "keywords": ["magkano", "price", "cost", "solar panel", "talesun", "585w", "620w", "how much", "presyo", "panel price", "solar price", "solar panels"],
        "answer_en": """☀️ **Solar Panel Pricing (Talesun):**

**620W Bifacial**
- Retail: ₱6,100/pc
- Installer price: ₱5,850/pc

**585W Bifacial**
- Retail: ₱5,750/pc
- Installer price: ₱5,650/pc

Contact us for bulk orders and special pricing! 📞""",
        "answer_tl": """☀️ **Presyo ng Solar Panels (Talesun):**

**620W Bifacial**
- Retail: ₱6,100/pc
- Installer price: ₱5,850/pc

**585W Bifacial**
- Retail: ₱5,750/pc
- Installer price: ₱5,650/pc

Makipag-ugnayan sa amin para sa bulk orders! 📞"""
    },
    
    "location": {
        "keywords": ["location", "located", "saan", "address", "office", "branch", "where", "lokasyon"],
        "answer_en": """📍 **Our Locations:**

**Main Office:**
Filinvest, Muntilupa City
[Google Map: UltiPhoton Solar Power OPC]

**Branch:**
UltiPhoton Solar Power Batangas
[Google Map: UltiPhoton Solar Power Batangas]

Feel free to visit us! ☀️""",
        "answer_tl": """📍 **Aming Mga Lokasyon:**

**Main Office:**
Filinvest, Muntilupa City
[Google Map: UltiPhoton Solar Power OPC]

**Branch:**
UltiPhoton Solar Power Batangas
[Google Map: UltiPhoton Solar Power Batangas]

Bisitahin kami anumang oras! ☀️"""
    },
    
    "cod": {
        "keywords": ["cod", "delivery", "cash on delivery", "available", "area", "deliver", "delivery"],
        "answer_en": """✅ **Cash on Delivery Available!**

We offer COD within **Batangas City area**.

We can also deliver to:
• Laguna
• Quezon Province
• Whole South Luzon

Contact us for delivery details! 🚚""",
        "answer_tl": """✅ **Cash on Delivery Available!**

Available ang COD sa loob ng **Batangas City area**.

Maaari din kaming magdeliver sa:
• Laguna
• Quezon Province
• Buong South Luzon

Makipag-ugnayan para sa delivery details! 🚚"""
    },
    
    "payment": {
        "keywords": ["payment", "pay", "bank", "transfer", "cash", "gcash", "paano", "bayad", "magbayad"],
        "answer_en": """💳 **Payment Methods:**

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

Please transfer and provide proof of payment! 🏦""",
        "answer_tl": """💳 **Paraan ng Pagbabayad:**

Tumatanggap lang kami ng **Bank Transfer** (Walang cash)

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

Magpadala ng proof of payment! 🏦"""
    },
    
    "accessories": {
        "keywords": ["railing", "mounting", "accessories", "breaker", "wire", "protection", "device", "meron",
                    "l foot", "mid clamp", "end clamp", "rail splicer", "grounding", "mc4", "spd",
                    "dc breaker", "ac breaker", "battery breaker", "clamp", "soeasy", "chint"],
        "answer_en": """🔧 **Accessories & Materials Price List:**

📌 **PV Mountings (SoEasy Brand):**
- Aluminum Railing 2.4m: ₱600/pc
- L Foot: ₱95/pc
- Mid Clamp: ₱85/pc
- End Clamp: ₱85/pc
- Rail Splicer: ₱85/pc
- PV Grounding Lug: ₱70/pc

📌 **DC Breakers (Chint/Chyt):**
- DC Breaker 20A, 2P: ₱680/pc

📌 **AC Breakers (Chint/Chyt):**
- AC Breaker 40A, 2P: ₱750/pc
- AC Breaker 63A, 2P: ₱750/pc
- AC Breaker 100A, 2P: ₱1,300/pc

📌 **Surge Protection (SPD):**
- DC SPD 1200VDC 40kA: ₱780/pc
- AC SPD 2P 400V: ₱580/pc
- AC SPD 4P 385V: ₱980/pc

📌 **Connectors & Others:**
- MC4 30A DC 1000V (Male & Female pair): ₱80/pair
- Battery Breaker DC 250AT: ₱1,700/pc

Contact us for bulk orders! ⚡""",
        "answer_tl": """🔧 **Listahan ng Presyo ng Accessories & Materials:**

📌 **PV Mountings (SoEasy Brand):**
- Aluminum Railing 2.4m: ₱600/pc
- L Foot: ₱95/pc
- Mid Clamp: ₱85/pc
- End Clamp: ₱85/pc
- Rail Splicer: ₱85/pc
- PV Grounding Lug: ₱70/pc

📌 **DC Breakers (Chint/Chyt):**
- DC Breaker 20A, 2P: ₱680/pc

📌 **AC Breakers (Chint/Chyt):**
- AC Breaker 40A, 2P: ₱750/pc
- AC Breaker 63A, 2P: ₱750/pc
- AC Breaker 100A, 2P: ₱1,300/pc

📌 **Surge Protection (SPD):**
- DC SPD 1200VDC 40kA: ₱780/pc
- AC SPD 2P 400V: ₱580/pc
- AC SPD 4P 385V: ₱980/pc

📌 **Connectors & Others:**
- MC4 30A DC 1000V (Male & Female pair): ₱80/pair
- Battery Breaker DC 250AT: ₱1,700/pc

Makipag-ugnayan para sa bulk orders! ⚡"""
    },
    
    "inverter_brands": {
        "keywords": ["inverter", "brand", "deye", "solis", "goodwe", "srne", "sigenergy", "ano mga"],
        "answer_en": """⚡ **Inverter Brands Available:**

✅ **Deye** - 5 years warranty
✅ **Solis** - 5 years warranty
✅ **GoodWe** - 5 years warranty
✅ **SRNE** - 5 years warranty
✅ **Sigenergy** - 10 years warranty

All brands are high-quality and reliable for Philippine climate! 🌞""",
        "answer_tl": """⚡ **Available Inverter Brands:**

✅ **Deye** - 5 taong warranty
✅ **Solis** - 5 taong warranty
✅ **GoodWe** - 5 taong warranty
✅ **SRNE** - 5 taong warranty
✅ **Sigenergy** - 10 taong warranty

Lahat ay high-quality at reliable! 🌞"""
    },
    
    "warranty": {
        "keywords": ["warranty", "years", "guarantee", "coverage", "ilang"],
        "answer_en": """✅ **Warranty Coverage:**

**Solar Panels (Talesun):**
10 years warranty

**Inverters:**
- Deye, Solis, SRNE, GoodWe: 5 years
- Sigenergy: 10 years

Quality guaranteed! ☀️""",
        "answer_tl": """✅ **Warranty Coverage:**

**Solar Panels (Talesun):**
10 taong warranty

**Inverters:**
- Deye, Solis, SRNE, GoodWe: 5 taon
- Sigenergy: 10 taon

Garantisadong kalidad! ☀️"""
    },
    
    "battery": {
        "keywords": ["battery", "storage", "backup", "energy storage", "may battery"],
        "answer_en": """🔋 **Battery Storage:**

Yes, we offer batteries **by order only**

We don't keep batteries in stock, but we can source them for you based on your requirements.

Contact us to discuss your battery needs! 📞""",
        "answer_tl": """🔋 **Battery Storage:**

Oo, nag-aalok kami ng batteries **by order lang**

Walang stock kami pero maaari naming kumuha para sa inyo.

Makipag-ugnayan para sa battery needs! 📞"""
    },
    
    "installation_time": {
        "keywords": ["installation", "how long", "days", "time", "duration", "gaano katagal"],
        "answer_en": """⏱️ **Installation Timeline:**

**Duration:** 1 day to 20 days

**Depends on:**
- Site conditions
- System complexity
- Weather conditions

We'll provide a specific timeline after site inspection! 🏗️""",
        "answer_tl": """⏱️ **Installation Timeline:**

**Duration:** 1 hanggang 20 araw

**Depende sa:**
- Site conditions
- System complexity
- Weather conditions

Magbibigay kami ng specific timeline pagkatapos ng inspection! 🏗️"""
    },
    
    "site_inspection": {
        "keywords": ["site inspection", "libre", "free", "survey", "inspect"],
        "answer_en": """🔍 **Site Inspection:**

✅ **FREE Site Inspection!**

We provide complimentary site inspection to assess your property and design the perfect solar system for you.

**Condition:** We hope you'll choose us for installation! 😊

Schedule your free inspection today! 📞""",
        "answer_tl": """🔍 **Site Inspection:**

✅ **LIBRE ang Site Inspection!**

Nag-aalok kami ng free inspection para malaman ang perfect solar system para sa inyo.

**Condition:** Sana kami ang pipiliin ninyo! 😊

Schedule ngayon! 📞"""
    },
    "full_pricelist": {
        "keywords": [
            "pricelist", "price list", "listahan ng presyo", "presyo ng lahat",
            "lahat ng presyo", "complete price", "full price", "all prices",
            "materials price", "magkano lahat", "ano lahat", "list of prices",
            "price ng materials", "presyo ng materials"
        ],
        "answer_en": """💰 **Ultiphoton Official Price List:**

☀️ **Solar Panels (Talesun):**
- 620W: ₱6,100 retail / ₱5,850 installer
- 585W: ₱5,750 retail / ₱5,650 installer

📌 **PV Mountings (SoEasy):**
- Aluminum Railing 2.4m: ₱600
- L Foot: ₱95 | Mid/End Clamp: ₱85
- Rail Splicer: ₱85 | Grounding Lug: ₱70

📌 **Breakers & Protection (Chint/Chyt):**
- DC Breaker 20A 2P: ₱680
- AC Breaker 40A/63A 2P: ₱750
- AC Breaker 100A 2P: ₱1,300
- DC SPD 1200V 40kA: ₱780
- AC SPD 2P 400V: ₱580
- AC SPD 4P 385V: ₱980

📌 **Connectors:**
- MC4 30A 1000V pair: ₱80
- Battery Breaker DC 250AT: ₱1,700

Contact us for bulk orders & inverter pricing! 📞""",
        "answer_tl": """💰 **Opisyal na Listahan ng Presyo ng Ultiphoton:**

☀️ **Solar Panels (Talesun):**
- 620W: ₱6,100 retail / ₱5,850 installer
- 585W: ₱5,750 retail / ₱5,650 installer

📌 **PV Mountings (SoEasy):**
- Aluminum Railing 2.4m: ₱600
- L Foot: ₱95 | Mid/End Clamp: ₱85
- Rail Splicer: ₱85 | Grounding Lug: ₱70

📌 **Breakers & Protection (Chint/Chyt):**
- DC Breaker 20A 2P: ₱680
- AC Breaker 40A/63A 2P: ₱750
- AC Breaker 100A 2P: ₱1,300
- DC SPD 1200V 40kA: ₱780
- AC SPD 2P 400V: ₱580
- AC SPD 4P 385V: ₱980

📌 **Connectors:**
- MC4 30A 1000V pair: ₱80
- Battery Breaker DC 250AT: ₱1,700

Makipag-ugnayan para sa bulk orders at inverter pricing! 📞"""
    },
    "products_and_price": {
        "keywords": [
            # English phrasings
            "what are your products", "what products", "products and price",
            "products and how much", "what do you sell", "what do you offer",
            "available products", "list of products", "product list",
            "what can i buy", "what items", "what materials",
            "show me your products", "show products", "your products",
            "anong products", "anong meron", "anong available",
            # Tagalog phrasings
            "ano ang mga produkto", "ano ang products", "ano ang ibinebenta",
            "ano ang meron kayo", "anong meron kayo", "ano ang available",
            "mga produkto at presyo", "produkto at presyo", "produkto at magkano",
            "ano ang binebenta", "ano ang ibinebenta ninyo", "anong binebenta",
            "ipakita ang products", "ipakita ang presyo", "lahat ng produkto",
            "mga available na produkto", "anong solar", "anong panels"
        ],
        # answer is built dynamically from Excel via get_faq_answer
        "answer_en": "[excel:full_pricelist]",
        "answer_tl": "[excel:full_pricelist]"
    },
    "website": {
        "keywords": [
            "website", "web site", "online", "link", "url", "site nyo", "webpage",
            "website nyo", "website ninyo", "website niyo", "website po", "website kayo",
            "ano website", "ano po website", "may website", "meron website",
            "your website", "your site", "your page", "your link",
            "ultiphoton.com", "ultiphotonsolar"
        ],
        "answer_en": """🌐 **Our Website:**

Visit us online at:
👉 https://ultiphotonsolarpoweropc.com/

You can find more information about our products, services, and solar solutions on our website! ☀️""",
        "answer_tl": """🌐 **Ang Aming Website:**

Bisitahin kami online sa:
👉 https://ultiphotonsolarpoweropc.com/

Makikita ninyo doon ang lahat ng impormasyon tungkol sa aming mga produkto at serbisyo! ☀️"""
    }
}

def detect_language(text):
    """Detect if message is in Tagalog or English"""
    tagalog_words = ["ang", "sa", "ng", "ko", "mo", "nyo", "kami", "tayo", "sila", "po", "ba", "kayo", "magkano", "saan", "paano", "ano", "ito", "yan", "dito", "doon", "nandito", "nandoon"]
    
    words = text.lower().split()
    tagalog_count = sum(1 for word in words if any(tl_word in word for tl_word in tagalog_words))
    
    # If more than 30% of words are Tagalog indicators, it's Tagalog
    if len(words) > 0 and tagalog_count / len(words) > 0.3:
        return "tl"
    return "en"

def save_user_language(user_id, language):
    """Save user's language preference"""
    try:
        with db_lock:
            conn = sqlite3.connect('/tmp/ultiphoton_chatbot.db')
            cursor = conn.cursor()
            cursor.execute('INSERT OR REPLACE INTO user_preferences (user_id, language) VALUES (?, ?)', (user_id, language))
            conn.commit()
            conn.close()
    except Exception as e:
        print(f"❌ Error saving language: {str(e)}")
        sys.stdout.flush()

def get_user_language(user_id):
    """Get user's saved language preference"""
    try:
        with db_lock:
            conn = sqlite3.connect('/tmp/ultiphoton_chatbot.db')
            cursor = conn.cursor()
            cursor.execute('SELECT language FROM user_preferences WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else "auto"
    except:
        return "auto"

def is_first_message(user_id):
    """Check if this is user's first message"""
    try:
        with db_lock:
            conn = sqlite3.connect('/tmp/ultiphoton_chatbot.db')
            cursor = conn.cursor()
            cursor.execute('SELECT first_message_sent FROM user_preferences WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            conn.close()
            return not result or not result[0]
    except:
        return True

def mark_first_message_sent(user_id):
    """Mark that first message has been sent to user"""
    try:
        with db_lock:
            conn = sqlite3.connect('/tmp/ultiphoton_chatbot.db')
            cursor = conn.cursor()
            cursor.execute('INSERT OR REPLACE INTO user_preferences (user_id, first_message_sent) VALUES (?, 1)', (user_id,))
            conn.commit()
            conn.close()
    except Exception as e:
        print(f"❌ Error marking first message: {str(e)}")
        sys.stdout.flush()

def save_conversation(user_id, message, response, language, faq_matched):
    """Save conversation to database for analytics"""
    try:
        with db_lock:
            conn = sqlite3.connect('/tmp/ultiphoton_chatbot.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO conversations (user_id, message, response, language, faq_matched)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, message, response, language, faq_matched))
            conn.commit()
            conn.close()
    except Exception as e:
        print(f"❌ Error saving conversation: {str(e)}")
        sys.stdout.flush()

def log_analytics(user_id, faq_key, keyword):
    """Log analytics for FAQ usage"""
    try:
        with db_lock:
            conn = sqlite3.connect('/tmp/ultiphoton_chatbot.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO analytics (user_id, faq_key, keyword) VALUES (?, ?, ?)', (user_id, faq_key, keyword))
            conn.commit()
            conn.close()
    except Exception as e:
        print(f"❌ Error logging analytics: {str(e)}")
        sys.stdout.flush()

def get_analytics_summary():
    """Get analytics summary for dashboard"""
    try:
        with db_lock:
            conn = sqlite3.connect('/tmp/ultiphoton_chatbot.db')
            cursor = conn.cursor()
            
            # Total conversations
            cursor.execute('SELECT COUNT(*) FROM conversations')
            total_conversations = cursor.fetchone()[0]
            
            # FAQ matches
            cursor.execute('SELECT COUNT(*) FROM conversations WHERE faq_matched = 1')
            faq_matches = cursor.fetchone()[0]
            
            # Most popular FAQs
            cursor.execute('''
                SELECT faq_key, COUNT(*) as count FROM analytics 
                GROUP BY faq_key ORDER BY count DESC LIMIT 5
            ''')
            popular_faqs = cursor.fetchall()
            
            # Language distribution
            cursor.execute('''
                SELECT language, COUNT(*) as count FROM conversations 
                GROUP BY language
            ''')
            language_dist = cursor.fetchall()
            
            conn.close()
            
            return {
                "total_conversations": total_conversations,
                "faq_matches": faq_matches,
                "popular_faqs": popular_faqs,
                "language_distribution": language_dist
            }
    except Exception as e:
        print(f"❌ Error getting analytics: {str(e)}")
        sys.stdout.flush()
        return {}

def is_business_hours():
    """Check if current time is within business hours (Philippine Time)"""
    from datetime import datetime, timezone, timedelta
    
    # Philippine Time is UTC+8
    ph_tz = timezone(timedelta(hours=8))
    current_time = datetime.now(ph_tz)
    current_hour = current_time.hour
    current_day = current_time.weekday()
    
    return (BUSINESS_HOURS["start"] <= current_hour < BUSINESS_HOURS["end"] and 
            current_day in BUSINESS_HOURS["days"])

def get_greeting_message(language):
    """Get auto-greeting message"""
    if language == "tl":
        return """👋 **Maligayang pagdating sa Ultiphoton Solar Power OPC!** ☀️

Kami ay nandito upang sagutin ang lahat ng inyong mga tanong tungkol sa solar panels at renewable energy solutions.

Paano namin kayo matutulungan ngayong araw? 🌞

Maaari kayong magtanong tungkol sa:
• 💰 Presyo ng Solar Panels
• 📍 Aming Lokasyon
• 💳 Paraan ng Pagbabayad
• 🔧 Accessories at Mounting
• ⚡ Inverter Brands
• 📦 Delivery at Installation

Salamat sa inyong interes! 💚"""
    else:
        return """👋 **Welcome to Ultiphoton Solar Power OPC!** ☀️

We're here to answer all your questions about solar panels and renewable energy solutions.

How can we help you today? 🌞

You can ask about:
• 💰 Solar Panel Pricing
• 📍 Our Locations
• 💳 Payment Methods
• 🔧 Accessories & Mounting
• ⚡ Inverter Brands
• 📦 Delivery & Installation

Thank you for your interest! 💚"""

def get_business_hours_message(language):
    """Legacy function kept for compatibility — now returns after-hours note."""
    return get_after_hours_note(language)

def get_after_hours_note(language):
    """Brief after-hours note appended to every response outside business hours."""
    if language == "tl":
        return ("🌙 *Paunawa:* Kami ay kasalukuyang nasa labas ng aming business hours "
                "(Mon–Sun, 8AM–6PM PH Time). Nakatanggap ka ng automated na sagot. "
                "Ang aming team ay mag-follow up sa iyo sa susunod na araw ng trabaho! 💚")
    else:
        return ("🌙 *Note:* We are currently outside our business hours "
                "(Mon–Sun, 8AM–6PM PH Time). You have received an automated reply. "
                "Our team will follow up with you on the next business day! 💚")

# Keywords that are specific to accessories/materials — must be checked BEFORE generic pricing keywords
ACCESSORY_SPECIFIC_KEYWORDS = {
    "railing", "railings", "mounting", "mountings", "l foot", "mid clamp", "end clamp",
    "rail splicer", "grounding lug", "grounding", "mc4", "spd", "dc breaker", "ac breaker",
    "battery breaker", "clamp", "soeasy", "chint", "chyt", "breaker", "surge protection",
    "connector", "connectors", "dc spd", "ac spd", "aluminum railing"
}

# Keywords that are specific to solar panels — must be checked BEFORE generic pricing keywords
SOLAR_SPECIFIC_KEYWORDS = {
    "solar panel", "solar panels", "talesun", "585w", "620w", "panel price", "solar price",
    "bifacial", "photovoltaic", "pv panel"
}

def find_matching_faq(user_message):
    """Find matching FAQ with priority: specific product keywords win over generic pricing words."""
    message_lower = user_message.lower()

    # --- PASS 1: Check accessories-specific keywords first ---
    # This prevents "magkano ang railings?" from matching solar_panel_price via "magkano"
    for kw in ACCESSORY_SPECIFIC_KEYWORDS:
        if kw in message_lower:
            return "accessories", FAQS["accessories"]

    # --- PASS 2: Check solar-panel-specific keywords ---
    for kw in SOLAR_SPECIFIC_KEYWORDS:
        if kw in message_lower:
            return "solar_panel_price", FAQS["solar_panel_price"]

    # --- PASS 3: Normal FAQ loop for all other FAQs (skipping accessories & solar_panel_price
    #             since they were already handled above) ---
    SKIP_IN_PASS3 = {"accessories", "solar_panel_price"}
    for faq_key, faq_data in FAQS.items():
        if faq_key in SKIP_IN_PASS3:
            continue
        for keyword in faq_data["keywords"]:
            if keyword.lower() in message_lower:
                return faq_key, faq_data

    # --- PASS 4: Fall back to accessories / solar_panel_price via generic keywords ---
    for faq_key in ("accessories", "solar_panel_price"):
        faq_data = FAQS[faq_key]
        for keyword in faq_data["keywords"]:
            if keyword.lower() in message_lower:
                return faq_key, faq_data

    return None, None

def get_faq_answer(faq_data, language, faq_key=None):
    """Get FAQ answer - uses live Excel data for pricing FAQs, static text for others."""
    # For pricing FAQs, always build answer from the Excel file
    if faq_key == "solar_panel_price":
        excel_answer = build_solar_panel_answer(language)
        if excel_answer:
            return excel_answer
    elif faq_key == "accessories":
        excel_answer = build_accessories_answer(language)
        if excel_answer:
            return excel_answer
    elif faq_key in ("full_pricelist", "products_and_price"):
        excel_answer = build_pricelist_answer(language)
        if excel_answer:
            return excel_answer

    # Fallback to static FAQ text for non-pricing FAQs or if Excel unavailable
    if language == "tl" and "answer_tl" in faq_data:
        return faq_data["answer_tl"]
    elif "answer_en" in faq_data:
        return faq_data["answer_en"]
    else:
        return faq_data.get("answer", "")

def get_quick_reply_buttons(language):
    """Get quick reply buttons for common questions"""
    if language == "tl":
        buttons = [
            {"title": "💰 Presyo", "payload": "presyo"},
            {"title": "📍 Lokasyon", "payload": "lokasyon"},
            {"title": "💳 Pagbabayad", "payload": "pagbabayad"},
            {"title": "⚡ Inverter", "payload": "inverter"},
            {"title": "🔧 Accessories", "payload": "accessories"},
            {"title": "📞 Makipag-ugnayan", "payload": "contact"}
        ]
    else:
        buttons = [
            {"title": "💰 Pricing", "payload": "pricing"},
            {"title": "📍 Location", "payload": "location"},
            {"title": "💳 Payment", "payload": "payment"},
            {"title": "⚡ Inverter", "payload": "inverter"},
            {"title": "🔧 Accessories", "payload": "accessories"},
            {"title": "📞 Contact", "payload": "contact"}
        ]
    return buttons

def get_ai_response(user_message, language):
    """Get AI response from OpenAI with FAQ context"""
    try:
        print(f"🤖 Processing: {user_message[:50]}... (Language: {language})")
        sys.stdout.flush()
        
        # Check for FAQ match first
        faq_key, faq_data = find_matching_faq(user_message)
        if faq_key and faq_data:
            print(f"✅ FAQ Match Found: {faq_key}")
            sys.stdout.flush()
            return get_faq_answer(faq_data, language, faq_key=faq_key), True, faq_key
        
        # If no FAQ match, use AI to generate response
        print(f"🤖 Using AI to generate response...")
        sys.stdout.flush()
        
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        system_message = """You are a helpful AI assistant for Ultiphoton Solar Power OPC, a solar panel company in the Philippines.

Company Information:
- Main Office: Filinvest, Muntilupa City
- Branch: Batangas
- Warehouse: Cainta
- Products: Talesun Solar Panels (585W, 620W), Inverters (Deye, Solis, GoodWe, SRNE, Sigenergy)
- Services: Installation, Maintenance, Consultation
- Delivery: COD available in Batangas, Laguna, Quezon, South Luzon
- Website: https://ultiphotonsolarpoweropc.com/

Guidelines:
1. Be friendly, professional, and helpful
2. Keep responses concise (under 100 words)
3. If you don't know specific details, suggest they contact the company
4. Always mention "Feel free to contact us!" at the end
5. Use emojis to make responses friendly ☀️⚡💚
6. IMPORTANT: NEVER quote any prices or peso amounts. You do not have access to the official price list.
   If asked about pricing, ALWAYS say: 'For our official price list, please ask: What is the price list?' or direct them to message the page.
7. All pricing information is handled by a separate FAQ system - do not attempt to answer price questions yourself."""
        
        if language == "tl":
            system_message += "\n8. Respond in Tagalog/Filipino"
        else:
            system_message += "\n7. Respond in English"
        
        payload = {
            "model": "gpt-4.1-mini",
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
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
            return ai_response, False, None
        else:
            print(f"❌ OpenAI Error: {response.status_code}")
            sys.stdout.flush()
            return "Sorry, I'm having trouble processing your request. Please try again or contact us directly! 📞", False, None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.stdout.flush()
        return "Sorry, I encountered an error. Please contact us directly! 📞", False, None

def send_typing_indicator(recipient_id):
    """Send typing indicator to show bot is processing"""
    try:
        url = f"https://graph.facebook.com/v19.0/{PAGE_ID}/messages"
        
        payload = {
            "recipient": {"id": recipient_id},
            "sender_action": "typing_on"
        }
        
        params = {"access_token": PAGE_ACCESS_TOKEN}
        
        response = requests.post(url, json=payload, params=params, timeout=5)
        return response.status_code == 200
    except:
        return False

def send_message_with_quick_replies(recipient_id, message_text, language):
    """Send message with quick reply buttons"""
    try:
        print(f"📤 Sending message with quick replies to {recipient_id}...")
        sys.stdout.flush()
        
        url = f"https://graph.facebook.com/v19.0/{PAGE_ID}/messages"
        
        quick_replies = get_quick_reply_buttons(language)
        
        payload = {
            "recipient": {"id": recipient_id},
            "message": {
                "text": message_text,
                "quick_replies": [
                    {
                        "content_type": "text",
                        "title": btn["title"],
                        "payload": btn["payload"]
                    }
                    for btn in quick_replies
                ]
            }
        }
        
        params = {"access_token": PAGE_ACCESS_TOKEN}
        
        response = requests.post(url, json=payload, params=params, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Message with quick replies sent!")
            sys.stdout.flush()
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            sys.stdout.flush()
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.stdout.flush()
        return False

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
        
        params = {"access_token": PAGE_ACCESS_TOKEN}
        
        response = requests.post(url, json=payload, params=params, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Message sent successfully!")
            sys.stdout.flush()
            return True
        else:
            print(f"❌ Facebook Error: {response.status_code}")
            sys.stdout.flush()
            return False
            
    except Exception as e:
        print(f"❌ Error sending message: {str(e)}")
        sys.stdout.flush()
        return False

@app.route("/", methods=["GET"])
def home():
    return "🤖 Ultiphoton Solar Power OPC Advanced Chatbot is running!", 200

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
                            
                            # Detect language
                            detected_lang = detect_language(message)
                            saved_lang = get_user_language(sender_id)
                            
                            if saved_lang == "auto":
                                language = detected_lang
                                save_user_language(sender_id, language)
                            else:
                                language = saved_lang
                            
                            print(f"🌍 Language: {language}")
                            sys.stdout.flush()
                            
                            # Send auto-greeting if first message
                            if is_first_message(sender_id):
                                greeting = get_greeting_message(language)
                                send_message_with_quick_replies(sender_id, greeting, language)
                                mark_first_message_sent(sender_id)
                                time.sleep(1)
                            
                            # 24/7 mode: always respond, but append after-hours note if outside business hours
                            after_hours_note = None
                            if not is_business_hours():
                                after_hours_note = get_after_hours_note(language)
                            
                            # Send typing indicator
                            send_typing_indicator(sender_id)
                            time.sleep(1)
                            
                            # Get AI response (with FAQ checking)
                            response_text, faq_matched, faq_key = get_ai_response(message, language)
                            
                            # Log analytics
                            if faq_matched and faq_key:
                                log_analytics(sender_id, faq_key, message)
                            
                            # Save conversation
                            save_conversation(sender_id, message, response_text, language, faq_matched)
                            
                            # Send response with quick replies
                            send_message_with_quick_replies(sender_id, response_text, language)
                            
                            # If outside business hours, send a brief follow-up note
                            if after_hours_note:
                                time.sleep(0.5)
                                send_message(sender_id, after_hours_note)
            
            return "EVENT_RECEIVED", 200
            
        except Exception as e:
            print(f"❌ Webhook Error: {str(e)}")
            sys.stdout.flush()
            return "ERROR", 500

@app.route("/analytics", methods=["GET"])
def analytics():
    """Analytics dashboard endpoint"""
    try:
        analytics_data = get_analytics_summary()
        return json.dumps(analytics_data, indent=2), 200, {"Content-Type": "application/json"}
    except Exception as e:
        return json.dumps({"error": str(e)}), 500, {"Content-Type": "application/json"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
