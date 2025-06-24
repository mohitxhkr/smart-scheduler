🧠 Smart Voice Scheduler
A voice/text-powered assistant that schedules meetings using Google Calendar. Built with Streamlit, Whisper, ElevenLabs, OpenRouter, and Google Calendar API for a seamless hands‑free experience.

🚀 Features
🎙️ Voice input via Whisper (speech-to-text)

🔊 Voice output via ElevenLabs TTS

🧠 Intent understanding via OpenRouter LLM

📅 Meeting scheduling in Google Calendar

🕒 Natural date parsing: supports both absolute ("17th June 2025 at 4 PM") and relative ("tomorrow at 3 PM")

✅ Confirmation flow before booking a meeting

🌐 Timezone-aware (IST – Asian/Kolkata)

💬 Chat history available in the web UI

🛠️ Tech Stack
Functionality	Library / Service
UI	Streamlit
LLM	OpenRouter (GPT-based)
ASR	OpenAI Whisper
TTS	ElevenLabs
Calendar Integration	Google Calendar API
Audio I/O	sounddevice, scipy, pygame
Date Parsing / TZ	dateparser, pytz

💾 Installation
bash
Copy
Edit
git clone https://github.com/mohitxhkr/smart-scheduler.git
cd smart-scheduler
python -m venv venv
# ✅ Windows
venv\Scripts\activate
# ✅ macOS/Linux
source venv/bin/activate
pip install -r requirements.txt
🔧 Setup
1. .env File
Create a .env file with:

ini
Copy
Edit
OPENROUTER_API_KEY=your_openrouter_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
2. Google Calendar Setup
Enable Calendar API via Google Cloud Console

Save your OAuth credentials as credentials.json in the project root

▶️ Run the App
Voice-enabled desktop interface:

bash
Copy
Edit
python main.py
Web interface:

bash
Copy
Edit
streamlit run app.py
🔍 Typical Workflow
Speak/type your intent:
“Schedule a call tomorrow at 3 PM”

The assistant:

Transcribes with Whisper

Understands intent via OpenRouter

Parses date/time (absolute or relative)

Asks for confirmation

Once confirmed:

Creates the event in your Google Calendar

Speaks/shows the confirmation and calendar link

💡 Example Interactions
“Schedule a meeting tomorrow at 4 PM”

“Book a call 17th June, 2025 at 11 AM”

“Show me my schedule”

“Stop” or “Exit” to close the session

📂 Folder Structure
bash
Copy
Edit
smart-scheduler/
├── .env
├── app.py
├── main.py
├── voice_agent.py
├── calendar_api.py
├── llm_engine.py
├── parse.py
├── credentials.json
└── requirements.txt
🛠️ Dependencies
Make sure these are installed:

nginx
Copy
Edit
streamlit
openai-whisper
sounddevice
pygame
scipy
python-dotenv
elevenlabs
torch
dateparser
pytz
google-api-python-client
google-auth-httplib2
google-auth-oauthlib
(All via requirements.txt)

🤔 FAQ
No audio? Ensure ffmpeg + mpv are installed and in PATH, and your speaker/mic are working.

Calendar not accessible? Verify permissions in credentials.json, and check your Google Cloud Console settings.

Misunderstanding time? The LLM handles parsing but date/string detection may fall back to manual parsing parse.py. Improve it for better edge-case handling.

