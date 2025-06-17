def speak(text, force_voice=True):
    print("Assistant:", text)
    try:
        if not force_voice:
            import streamlit as st
            st.markdown(f"**Assistant:** {text}")
            return
    except ImportError:
        pass

    try:
        import pyttsx3
        engine = pyttsx3.init(driverName='sapi5')  # Use 'nsss' on Mac, 'espeak' on Linux
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"Voice output failed: {e}")
