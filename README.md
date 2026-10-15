# 🤖 WhatsApp AI Chatbot & Custom Dataset Studio

An intelligent, production-ready WhatsApp Chatbot powered by your own customizable dataset. It includes:
1. **Interactive WhatsApp Web Simulator & Studio UI** (runs in your browser with zero setup, authentic WhatsApp dark/light mode, live message testing, typing indicators, quick reply pills).
2. **Modular Dataset Management**: Drop in any **JSON** or **CSV** dataset, or add/edit Q&A pairs directly in the web UI.
3. **Advanced Typo-Tolerant & Semantic Matching Engine**: Uses token alignment, SequenceMatcher fuzzy ratios, TF-IDF weighting, and dynamic entity extraction (e.g. tracking orders like `ORD-4892`).
4. **Dual Production Webhook Endpoints**:
   - Official **Meta WhatsApp Cloud API** (`GET & POST /webhook`)
   - **Twilio WhatsApp API** (`POST /twilio/webhook`)

---

## ⚡ Quick Start

### 1. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 2. Launch the Application
```bash
python app.py
```
Open **[http://localhost:5000](http://localhost:5000)** in your browser!

---

## 📂 Using Your Own Dataset

You can provide your own dataset using **either** of these methods:

### Method A: Upload Directly from the Web Interface
1. Click **"Dataset Manager"** in the top right.
2. Click **"Upload Custom File (.json / .csv)"** or drag and drop your file.
3. The chatbot will instantly re-index your knowledge base and start replying!

### Method B: Provide a JSON Dataset File
Save your dataset file into the `data/` folder (e.g. `data/my_company_dataset.json`):
```json
{
  "bot_name": "My Brand Bot",
  "bot_tagline": "24/7 Customer Care",
  "category": "Customer Support",
  "welcome_message": "Hello! 👋 Welcome to My Brand Bot. How can I help you?",
  "fallback_message": "Sorry, I didn't understand that. Here are some topics I can answer:",
  "quick_replies": ["Track Order", "Pricing", "Contact Us"],
  "knowledge_base": [
    {
      "id": "kb_pricing",
      "intent": "pricing_plans",
      "patterns": ["pricing", "how much does it cost", "plans", "subscription fees"],
      "response": "Our basic plan is $19/mo and Pro plan is $49/mo with unlimited access!",
      "quick_replies": ["Features", "Free Trial", "Speak to Sales"]
    }
  ]
}
```

### Method C: Provide a Simple CSV / Excel File
You can also drop a flat CSV spreadsheet into `data/my_faq.csv`:
```csv
question,answer,category,quick_replies
"What are your business hours?","We are open Mon-Fri from 9 AM to 6 PM.","General","Contact Info;Pricing"
"How can I request a refund?","Refunds are processed within 3 days by emailing billing@example.com.","Billing","Refund Policy;Support"
```

---

## 🔌 Connecting to Real WhatsApp

### Option 1: Official Meta WhatsApp Cloud API (Free 1,000 conversations/mo)
1. Go to [developers.facebook.com](https://developers.facebook.com) > **Create App** > Choose **Other > Business**.
2. Click **Set Up WhatsApp**. Meta gives you a free sandbox test phone number.
3. Expose your local port 5000 to the web:
   ```bash
   ngrok http 5000
   ```
4. In Meta Dashboard > **WhatsApp > Configuration > Webhook**:
   - **Callback URL:** `https://your-ngrok-subdomain.ngrok-free.app/webhook`
   - **Verify Token:** `my_secret_whatsapp_verify_token_2026` (or set custom in `.env`)
   - Subscribe to the `messages` field.
5. In your `.env` file (copy from `.env.example`), fill in:
   ```env
   WHATSAPP_CLOUD_TOKEN=your_meta_system_user_access_token
   PHONE_NUMBER_ID=your_whatsapp_phone_number_id
   ```

### Option 2: Twilio WhatsApp Sandbox
1. Go to [console.twilio.com](https://console.twilio.com) > **Messaging > Try WhatsApp Sandbox**.
2. Set the *“When a message comes in”* webhook URL to:
   ```
   https://your-ngrok-subdomain.ngrok-free.app/twilio/webhook
   ```
3. Send the sandbox join phrase from your personal WhatsApp to Twilio’s phone number. Your custom dataset bot will reply immediately!

---

## 🧠 Smart NLP Features
- **Dynamic Entity Extraction**: Type `Track ORD-4892` and the bot detects the order number and returns live simulated courier tracking.
- **Typo Tolerance**: Handles common misspellings like *"retun polic"* -> matches *Return Policy*, *"lapotp"* -> matches *Laptops*.
- **Quick-Reply Suggestions**: Generates interactive WhatsApp button options dynamically.
- **Analytics & Trigger Frequency**: Monitor match rates and top triggered customer intents in the Analytics tab.
