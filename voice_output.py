import platform

def speak(text, force_voice=True):
    print("Assistant:", text)

    if not force_voice:
        # Optional integration with a web UI (like Streamlit)
        try:
            import streamlit as st
            st.markdown(f"**Assistant:** {text}")
            return
        except ImportError:
            pass

    try:
        import pyttsx3

        system = platform.system()
        # Select driver based on OS
        if system == "Windows":
            engine = pyttsx3.init(driverName='sapi5')
        elif system == "Darwin":  # macOS
            engine = pyttsx3.init(driverName='nsss')
        else:  # Linux and others
            engine = pyttsx3.init(driverName='espeak')

        engine.say(text)
        engine.runAndWait()

    except Exception as e:
        print(f"🔇 Voice output failed: {e}")
