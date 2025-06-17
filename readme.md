# 🧠 Smart Voice Scheduler with Streamlit + OpenRouter + Google Calendar

A smart assistant to schedule your meetings using natural voice/text input. Powered by OpenRouter (LLM), Streamlit for UI, and Google Calendar for scheduling.

---

## 🚀 Features
- 🎤 Voice + text input
- 🧠 AI-powered understanding (via OpenRouter)
- 📅 Automatic meeting scheduling in Google Calendar
- 🕒 Supports absolute ("17th June, 2025 at 4 PM") and vague ("tomorrow at 3 PM") date formats
- ✅ Timezone-aware (IST - India Standard Time)
- 💬 Chat history + confirmation before booking

---

## 🛠️ Tech Stack
- **Python 3.9+**
- **Streamlit** – UI
- **OpenRouter** – LLM API (GPT-3.5 Turbo, etc.)
- **Google Calendar API** – Meeting creation
- **SpeechRecognition** – Voice input
- **pyttsx3** – Text-to-speech output
- **dateparser + pytz** – Date/time parsing

---

## 📦 Installation
```bash
git clone https://github.com/your-repo/smart-scheduler.git
cd smart-scheduler
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## 🔐 Setup
### 1. `.env` file
```
OPENROUTER_API_KEY=your_api_key_here
```

### 2. Google Calendar Credentials
- Get credentials from: https://console.cloud.google.com/
- Enable Calendar API
- Save as `credentials.json` in project root

---

## ▶️ Running the App
```bash
streamlit run app.py
```

---

## ✨ Usage
1. Enter or speak a meeting request
2. AI will understand your intent
3. Confirm scheduling details
4. Meeting is added to your Google Calendar

---

## 🙋 FAQ
- **Can I change the time format?** – Supports both 12h and vague formats
- **Does it speak back?** – Works on desktop, replaced with text in web UI
- **How do I invite others?** – Coming soon! (email invitee feature)
