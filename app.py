import streamlit as st
from llm_engine import generate_response
from voice_input import listen
from voice_output import speak
from calendar_api import authenticate_google_calendar, create_meeting
from datetime import datetime
import pytz
import dateparser
import re

IST = pytz.timezone("Asia/Kolkata")

def parse_datetime_from_text(text):
    if not text:
        return None

    # Match explicit format like: "17th June, 2025 at 4:00 PM"
    pattern = r"(\d{1,2}(?:st|nd|rd|th)?\s+\w+,\s*\d{4})\s*(?:at)?\s*(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))"
    match = re.search(pattern, text)
    if match:
        full = f"{match.group(1)} {match.group(2)}"
        parsed = dateparser.parse(full, settings={
            'TIMEZONE': 'Asia/Kolkata',
            'RETURN_AS_TIMEZONE_AWARE': True
        })
        if parsed and parsed > datetime.now(IST):
            return parsed

    # Fallback for natural phrases: "tomorrow at 4 PM", "next Friday"
    parsed = dateparser.parse(text, settings={
        'TIMEZONE': 'Asia/Kolkata',
        'RETURN_AS_TIMEZONE_AWARE': True,
        'PREFER_DATES_FROM': 'future'
    })
    if parsed and parsed > datetime.now(IST):
        return parsed

    return None

st.set_page_config(page_title="Smart Scheduler AI", layout="wide")
st.title("🧠 Smart Scheduler AI")
st.caption("Talk or type to schedule meetings effortlessly with your calendar")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

calendar_service = authenticate_google_calendar()
input_method = st.radio("Input method:", ["🎙️ Voice", "⌨️ Text"])

user_input = ""

# Voice input section
if input_method == "🎙️ Voice":
    if st.button("🎤 Click Here To Speak"):
        with st.spinner("Listening..."):
            try:
                user_input = listen()
                st.success(f"You said: {user_input}")
            except Exception as e:
                st.error("Microphone error or speech not recognized.")

# Text input section
elif input_method == "⌨️ Text":
    user_input = st.text_input("💬 Type your request here")

# Parse datetime from LLM/user message
def parse_datetime_from_text(text):
    if not text:
        return None

    # Match: "17th June, 2025 at 10:30 PM"
    regex = r"(\d{1,2}(?:st|nd|rd|th)?\s+\w+,\s*\d{4}).*?(\d{1,2}:\d{2}\s*(AM|PM|am|pm))"
    match = re.search(regex, text)
    if match:
        combined = f"{match.group(1)} {match.group(2)}"
        dt = dateparser.parse(combined, settings={'TIMEZONE': 'Asia/Kolkata', 'RETURN_AS_TIMEZONE_AWARE': True})
        return dt

    # Fallback: "tomorrow at 4 PM"
    dt = dateparser.parse(text, settings={
        'TIMEZONE': 'Asia/Kolkata',
        'RETURN_AS_TIMEZONE_AWARE': True,
        'PREFER_DATES_FROM': 'future'
    })
    return dt


# Run LLM and calendar scheduling
if user_input:
    st.session_state.chat_history.append(("You", user_input))
    with st.spinner("Thinking..."):
        try:
            bot_reply = generate_response(user_input)
        except Exception:
            bot_reply = "Sorry, there was an error with the language model."
    st.session_state.chat_history.append(("Assistant", bot_reply))
    speak(bot_reply)

    st.markdown("### 💡 Assistant Suggestion")
    st.markdown(f"**🤖:** {bot_reply}")

    parsed_time = parse_datetime_from_text(user_input) or parse_datetime_from_text(bot_reply)
    if parsed_time and parsed_time > datetime.now(IST):
        formatted_time = parsed_time.strftime("%d %B, %Y at %I:%M %p")
        if st.checkbox(f"✅ Confirm scheduling on {formatted_time}?"):
            meeting_title = st.text_input("📝 Meeting Title", "Smart Scheduler Meeting")
            duration = st.slider("⏱ Duration (minutes)", 15, 120, 60)
            if st.button("📅 Schedule Meeting"):
                try:
                    link = create_meeting(calendar_service, parsed_time.isoformat(), duration, summary=meeting_title)
                    st.success("✅ Meeting scheduled successfully!")
                    st.write(f"🔗 [Open in Google Calendar]({link})")
                except Exception as e:
                    st.error(f"Failed to schedule: {e}")
    else:
        st.info("❗ Couldn't parse a valid future date/time. Try: '17th June 2025 at 4:00 PM'.")

# Display chat history
st.markdown("---")
st.subheader("🗨️ Conversation History")
for sender, message in st.session_state.chat_history:
    st.markdown(f"**{sender}:** {message}")

if st.button("🗑️ Clear Conversation"):
    st.session_state.chat_history.clear()
    st.success("Conversation cleared.")
