import streamlit as st
from llm_engine import generate_response
from voice_input import listen
from voice_output import speak
from calendar_api import authenticate_google_calendar

# Configure Streamlit
st.set_page_config(page_title="Smart Scheduler AI", layout="wide")
st.title("🧠 Smart Scheduler AI Agent")
st.caption("Talk or type to schedule your meetings")

# Setup calendar service (optional, use later)
calendar_service = authenticate_google_calendar()

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Choose input method
input_method = st.radio("Choose input method:", ("🎙️ Microphone", "⌨️ Text Input"))

# Prepare user_input safely
user_input = ""

# Microphone input
if input_method == "🎙️ Microphone":
    if st.button("Click to Speak"):
        with st.spinner("Listening..."):
            user_input = listen()
            st.success(f"Recognized: {user_input}")

# Text input
elif input_method == "⌨️ Text Input":
    user_input = st.text_input("Type your message:")

# Process and respond
if user_input and user_input.strip():
    st.session_state.chat_history.append(("user", user_input))

    with st.spinner("Thinking..."):
        bot_reply = generate_response(user_input)
        st.session_state.chat_history.append(("assistant", bot_reply))
        speak(bot_reply)

# Display chat history
st.markdown("### 💬 Conversation")
for sender, message in st.session_state.chat_history:
    if sender == "user":
        st.markdown(f"**🧑 You:** {message}")
    else:
        st.markdown(f"**🤖 Assistant:** {message}")
