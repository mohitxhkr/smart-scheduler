import streamlit as st
from datetime import datetime
from calendar_api import authenticate_google_calendar, list_events, create_meeting
from main import parse_datetime_from_text
from llm_engine import generate_response
from voice_agent import (
    record_until_silence,
    transcribe_audio,
    synthesize_and_speak,
    synthesize_speech,
    play_audio
)
import re
import pytz

IST = pytz.timezone("Asia/Kolkata")

st.set_page_config(page_title="🧠 Smart Scheduler", layout="centered")
st.title("🧠 Voice-Controlled Smart Scheduler")

if "calendar_service" not in st.session_state:
    st.session_state.calendar_service = authenticate_google_calendar()

if "conversation_context" not in st.session_state:
    st.session_state.conversation_context = ""

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

input_method = st.radio("Choose Input Method:", ["🎙️ Voice", "⌨️ Text"])
start_triggered = st.button("🚀 Start Assistant")

def listen_and_transcribe():
    audio_path = record_until_silence()
    return transcribe_audio(audio_path)

if start_triggered:
    synthesize_and_speak("Hi! I’m your Smart Scheduler assistant. How can I help you today?")
    st.markdown("**Assistant:** Hi! I’m your Smart Scheduler assistant. How can I help you today?")

    while True:
        if input_method == "🎙️ Voice":
            with st.spinner("🎙 Listening..."):
                user_input = listen_and_transcribe()
        else:
            user_input = st.text_input("Type your command:", key="text_input")
            if user_input == "":
                st.stop()

        st.markdown(f"**You:** {user_input}")
        st.session_state.chat_history.append(("User", user_input))

        if any(word in user_input.lower() for word in ["stop", "exit"]):
            synthesize_and_speak("Okay, ending the session. Goodbye!")
            st.markdown("**Assistant:** Okay, ending the session. Goodbye!")
            break

        if "show" in user_input.lower() and "schedule" in user_input.lower():
            synthesize_and_speak("Here are your upcoming meetings.")
            events = list_events(st.session_state.calendar_service)

            if not events:
                st.markdown("No upcoming events found.")
                synthesize_and_speak("You have no upcoming meetings.")
                continue

            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                summary = event.get('summary', 'No title')
                time_obj = datetime.fromisoformat(start).astimezone(IST)
                formatted_time = time_obj.strftime("%d %B, %Y at %I:%M %p")
                st.markdown(f"**{summary}** on {formatted_time}")
                synthesize_and_speak(f"{summary} on {formatted_time}")
            continue

        st.session_state.conversation_context += f"\nUser: {user_input}"
        bot_reply = generate_response(user_input)
        synthesize_and_speak(bot_reply)
        st.markdown(f"**Assistant:** {bot_reply}")
        st.session_state.chat_history.append(("Assistant", bot_reply))
        st.session_state.conversation_context += f"\nAssistant: {bot_reply}"

        scheduled_time = parse_datetime_from_text(user_input) or parse_datetime_from_text(bot_reply)

        if scheduled_time:
            formatted = scheduled_time.strftime("%d %B, %Y at %I:%M %p")
            synthesize_and_speak(f"Should I schedule the meeting on {formatted}?")
            st.markdown(f"**Assistant:** Should I schedule the meeting on {formatted}?")

            if input_method == "🎙️ Voice":
                with st.spinner("🎙 Listening for confirmation..."):
                    confirm = listen_and_transcribe().lower()
            else:
                confirm = st.text_input("Confirm (yes / no):", key="confirm_input").lower()
                if confirm == "":
                    st.stop()

            if any(word in confirm for word in ["yes", "sure", "okay", "go ahead"]):
                if input_method == "⌨️ Text":
                    with st.form("schedule_form"):
                        meeting_title = st.text_input("Enter meeting title:", key="title_input")
                        duration_input = st.text_input("Enter meeting duration:", key="duration_input").lower()
                        submitted = st.form_submit_button("📅 Schedule Meeting")
                    if not submitted:
                        st.stop()
                else:
                    synthesize_and_speak("What should be the meeting title?")
                    with st.spinner("🎙 Listening for title..."):
                        meeting_title = listen_and_transcribe()

                    synthesize_and_speak("How long should the meeting be? For example, say '1 hour' or '30 minutes'.")
                    with st.spinner("🎙 Listening for duration..."):
                        duration_input = listen_and_transcribe().lower()

                hours = re.search(r"(\d+)\s*hour", duration_input)
                minutes = re.search(r"(\d+)\s*minute", duration_input)

                if hours and minutes:
                    duration = int(hours.group(1)) * 60 + int(minutes.group(1))
                elif hours:
                    duration = int(hours.group(1)) * 60
                elif minutes:
                    duration = int(minutes.group(1))
                else:
                    match = re.search(r"\d+", duration_input)
                    duration = int(match.group()) if match else 60

                link = create_meeting(
                    st.session_state.calendar_service,
                    scheduled_time.isoformat(),
                    duration,
                    summary=meeting_title
                )
                synthesize_and_speak("Your meeting has been scheduled. Here is the link.")
                st.markdown(f"[📅 Meeting Link]({link})")

                if input_method == "⌨️ Text":
                    st.session_state.title_input = ""
                    st.session_state.duration_input = ""
                    st.session_state.confirm_input = ""
                break
            else:
                synthesize_and_speak("Okay, I won’t schedule it yet.")
                continue
        else:
            synthesize_and_speak("I didn't catch the meeting time. Could you please say it again?")

st.markdown("---")
st.subheader("🗨️ Conversation History")
for sender, message in st.session_state.chat_history:
    st.markdown(f"**{sender}:** {message}")

if st.button("🗑️ Clear Conversation"):
    st.session_state.chat_history.clear()
    st.success("Conversation cleared.")
