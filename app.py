import streamlit as st
import threading
import time
from datetime import datetime
import re

# Import your existing modules
from voice_agent import record_until_silence, transcribe_audio, synthesize_speech, play_audio
from llm_engine import generate_response
from calendar_api import authenticate_google_calendar, create_meeting
from main import parse_datetime_from_text, synthesize_and_speak

# Page configuration
st.set_page_config(page_title="Smart Scheduler AI", page_icon="🤖", layout="wide")

# Compact CSS
st.markdown("""
<style>
    .main { padding: 0.5rem; font-size: 0.85rem; }
    .chat-message { padding: 0.5rem; border-radius: 8px; margin: 0.3rem 0; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .user-message { background: #667eea; color: white; margin-left: 1rem; }
    .assistant-message { background: #4facfe; color: white; margin-right: 1rem; }
    .system-message { background: #a8edea; color: #333; text-align: center; }
    .meeting-link { background: #00b894; color: white; padding: 0.8rem; border-radius: 10px; margin: 0.5rem 0; text-align: center; }
    .meeting-link a { color: white; text-decoration: none; font-weight: bold; }
    .status-display { background: rgba(255,255,255,0.9); padding: 0.5rem; border-radius: 8px; text-align: center; font-weight: bold; margin: 0.5rem 0; }
    .status-listening { background: #ff6b6b; color: white; animation: pulse 1s infinite; }
    .status-processing { background: #feca57; color: white; }
    .status-ready { background: #1dd1a1; color: white; }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    defaults = {
        'conversation_history': [],
        'calendar_service': None,
        'is_active': False,
        'current_step': 'ready',
        'meeting_step': 'none',  # none -> time -> title -> duration -> confirm -> create
        'temp_meeting': {},
        'text_input_key': 0
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def add_message(role: str, content: str, link: str = None):
    message = {
        'role': role,
        'content': content,
        'timestamp': datetime.now(),
        'link': link
    }
    st.session_state.conversation_history.append(message)
    
    # Keep only last 8 messages
    if len(st.session_state.conversation_history) > 8:
        st.session_state.conversation_history = st.session_state.conversation_history[-8:]

def display_conversation():
    if not st.session_state.conversation_history:
        st.markdown("""
        <div class="chat-message system-message">
            <h4>🤖 Smart Scheduler Ready!</h4>
            <p>Say something like: "Schedule a meeting tomorrow at 2 PM"</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    for msg in st.session_state.conversation_history:
        role_icon = {"user": "👤", "assistant": "🤖", "system": "ℹ️"}[msg['role']]
        css_class = f"{msg['role']}-message"
        timestamp = msg['timestamp'].strftime("%H:%M")
        
        st.markdown(f"""
        <div class="chat-message {css_class}">
            <div style="display: flex; justify-content: space-between;">
                <strong>{role_icon} {msg['role'].title()}</strong>
                <small>{timestamp}</small>
            </div>
            <p style="margin: 0.2rem 0;">{msg['content']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if msg.get('link'):
            st.markdown(f"""
            <div class="meeting-link">
                📅 Meeting Created! <a href="{msg['link']}" target="_blank">🔗 Join Meeting</a>
            </div>
            """, unsafe_allow_html=True)

def display_status():
    status_map = {
        'ready': ('🟢 Ready - Say something!', 'status-ready'),
        'listening': ('🎙️ Listening...', 'status-listening'),
        'processing': ('⚙️ Processing...', 'status-processing'),
    }
    
    text, css_class = status_map.get(st.session_state.current_step, ('🟢 Ready', 'status-ready'))
    
    st.markdown(f"""
    <div class="status-display {css_class}">
        {text}
    </div>
    """, unsafe_allow_html=True)

def extract_duration(text):
    """Extract meeting duration from text"""
    # Default to 60 minutes
    duration = 60
    
    # Extract numbers
    hours = re.search(r"(\d+)\s*hour", text.lower())
    minutes = re.search(r"(\d+)\s*minute", text.lower())
    
    if hours and minutes:
        duration = int(hours.group(1)) * 60 + int(minutes.group(1))
    elif hours:
        duration = int(hours.group(1)) * 60
    elif minutes:
        duration = int(minutes.group(1))
    else:
        # Look for any number
        match = re.search(r"\d+", text)
        if match:
            num = int(match.group())
            # If number is less than 10, assume hours, otherwise minutes
            duration = num * 60 if num <= 5 else num
    
    return duration

def handle_meeting_flow(user_input):
    """Handle the meeting creation flow step by step"""
    
    if st.session_state.meeting_step == 'none':
        # Check if user wants to schedule a meeting
        scheduled_time = parse_datetime_from_text(user_input)
        if scheduled_time:
            st.session_state.temp_meeting = {'datetime': scheduled_time}
            st.session_state.meeting_step = 'title'
            formatted = scheduled_time.strftime("%B %d, %Y at %I:%M %p")
            response = f"I'll schedule a meeting for {formatted}. What should be the meeting title?"
            add_message("assistant", response)
            synthesize_and_speak(response)
            return True
    
    elif st.session_state.meeting_step == 'title':
        # Get meeting title
        st.session_state.temp_meeting['title'] = user_input.strip()
        st.session_state.meeting_step = 'duration'
        response = "How long should the meeting be? You can say '1 hour', '30 minutes', etc."
        add_message("assistant", response)
        synthesize_and_speak(response)
        return True
    
    elif st.session_state.meeting_step == 'duration':
        # Get meeting duration
        duration = extract_duration(user_input)
        st.session_state.temp_meeting['duration'] = duration
        st.session_state.meeting_step = 'confirm'
        
        # Show summary for confirmation
        meeting = st.session_state.temp_meeting
        formatted_time = meeting['datetime'].strftime("%B %d, %Y at %I:%M %p")
        duration_text = f"{duration} minutes" if duration < 60 else f"{duration//60} hour{'s' if duration > 60 else ''}"
        
        response = f"Ready to create: '{meeting['title']}' on {formatted_time} for {duration_text}. Should I create it?"
        add_message("assistant", response)
        synthesize_and_speak(response)
        return True
    
    elif st.session_state.meeting_step == 'confirm':
        # Confirm and create meeting
        if any(word in user_input.lower() for word in ["yes", "sure", "okay", "go ahead", "create"]):
            create_meeting_now()
        else:
            st.session_state.meeting_step = 'none'
            st.session_state.temp_meeting = {}
            response = "Okay, I won't create the meeting. Anything else I can help with?"
            add_message("assistant", response)
            synthesize_and_speak(response)
        return True
    
    return False

def create_meeting_now():
    """Create the meeting with collected information"""
    try:
        if not st.session_state.calendar_service:
            st.session_state.calendar_service = authenticate_google_calendar()
        
        meeting = st.session_state.temp_meeting
        link = create_meeting(
            st.session_state.calendar_service,
            meeting['datetime'].isoformat(),
            meeting['duration'],
            summary=meeting['title']
        )
        
        success_msg = f"✅ Meeting '{meeting['title']}' created successfully!"
        add_message("system", success_msg, link=link)
        synthesize_and_speak("Your meeting has been created! The link is in the chat.")
        
    except Exception as e:
        error_msg = f"❌ Failed to create meeting: {str(e)[:50]}..."
        add_message("system", error_msg)
        synthesize_and_speak("Sorry, there was a problem creating the meeting.")
    
    # Reset meeting flow
    st.session_state.meeting_step = 'none'
    st.session_state.temp_meeting = {}

def handle_voice_interaction():
    """Main voice interaction handler"""
    try:
        # Listen for audio
        st.session_state.current_step = 'listening'
        audio_path = record_until_silence()
        
        if not audio_path:
            st.session_state.current_step = 'ready'
            return
        
        # Transcribe
        st.session_state.current_step = 'processing'
        user_text = transcribe_audio(audio_path)
        
        if not user_text:
            st.session_state.current_step = 'ready'
            return
        
        add_message("user", user_text)
        
        # Check for goodbye
        if any(word in user_text.lower() for word in ["thank you", "thanks", "goodbye", "bye", "stop", "exit"]):
            response = "Thank you! Have a wonderful day!"
            add_message("assistant", response)
            synthesize_and_speak(response)
            st.session_state.is_active = False
            st.session_state.current_step = 'ready'
            return
        
        # Handle meeting flow
        if handle_meeting_flow(user_text):
            st.session_state.current_step = 'ready'
            return
        
        # Generate normal response
        bot_reply = generate_response(user_text)
        add_message("assistant", bot_reply)
        synthesize_and_speak(bot_reply)
        
        st.session_state.current_step = 'ready'
        
    except Exception as e:
        add_message("system", f"Error: {str(e)[:50]}...")
        st.session_state.current_step = 'ready'

def process_text_input(text: str):
    """Process text input with same logic as voice"""
    add_message("user", text)
    
    # Check goodbye
    if any(word in text.lower() for word in ["thank you", "thanks", "goodbye", "bye", "stop", "exit"]):
        response = "Thank you! Have a wonderful day!"
        add_message("assistant", response)
        threading.Thread(target=lambda: synthesize_and_speak(response), daemon=True).start()
        return
    
    # Handle meeting flow
    if handle_meeting_flow(text):
        return
    
    # Generate normal response
    bot_reply = generate_response(text)
    add_message("assistant", bot_reply)
    threading.Thread(target=lambda: synthesize_and_speak(bot_reply), daemon=True).start()

def main():
    """Main application"""
    init_session_state()
    
    # Initialize calendar service
    if st.session_state.calendar_service is None:
        try:
            st.session_state.calendar_service = authenticate_google_calendar()
        except:
            st.session_state.calendar_service = None
    
    # Header
    st.markdown("""
    <div style="text-align: center; padding: 1rem;">
        <h1>🤖 Smart Scheduler AI</h1>
        <p>Voice-powered meeting assistant</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Status
        if st.session_state.is_active:
            display_status()
        
        # Conversation
        st.markdown("### 💬 Conversation")
        display_conversation()
        
        # Text input
        st.markdown("### ⌨️ Text Input")
        user_input = st.text_input("Message:", key=f"text_{st.session_state.text_input_key}")
        
        col_send, col_clear = st.columns(2)
        with col_send:
            if st.button("📤 Send") and user_input.strip():
                process_text_input(user_input.strip())
                st.session_state.text_input_key += 1
                st.rerun()
        
        with col_clear:
            if st.button("🗑️ Clear"):
                st.session_state.conversation_history = []
                st.session_state.meeting_step = 'none'
                st.session_state.temp_meeting = {}
                st.session_state.text_input_key += 1
                st.rerun()
    
    with col2:
        st.markdown("### 🎛️ Controls")
        
        # Voice controls
        if not st.session_state.is_active:
            if st.button("🚀 Start Voice", use_container_width=True):
                st.session_state.is_active = True
                st.session_state.current_step = 'ready'
                greeting = "Hello! I'm ready to help you schedule meetings!"
                add_message("assistant", greeting)
                threading.Thread(target=lambda: synthesize_and_speak(greeting), daemon=True).start()
                st.rerun()
        else:
            if st.button("⏹️ Stop Voice", use_container_width=True):
                st.session_state.is_active = False
                st.session_state.current_step = 'ready'
                add_message("system", "Voice session stopped")
                st.rerun()
        
        # Status dashboard
        st.markdown("### 📊 Status")
        
        if st.session_state.is_active:
            st.success("🟢 Voice Active")
        else:
            st.info("⚪ Voice Inactive")
        
        if st.session_state.meeting_step != 'none':
            st.warning(f"📅 Meeting Step: {st.session_state.meeting_step}")
        
        if st.session_state.calendar_service:
            st.success("📅 Calendar Connected")
        else:
            st.error("📅 Calendar Error")
        
        # Help
        st.markdown("### 💡 Help")
        st.markdown("""
        **Try saying:**
        - "Schedule meeting tomorrow 2PM"
        - "Book a call next Monday at 10 AM"
        - "Set up meeting Friday 3:30 PM"
        
        **Flow:**
        1. 🕐 Time detection
        2. 📝 Meeting title
        3. ⏱️ Duration
        4. ✅ Confirmation
        5. 🔗 Meeting created!
        """)
    
    # Voice interaction loop
    if st.session_state.is_active and st.session_state.current_step == 'ready':
        handle_voice_interaction()
        st.rerun()

if __name__ == "__main__":
    main()