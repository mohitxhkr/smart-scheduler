import speech_recognition as sr

def listen():
    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            print("🎙️ Listening...")
            recognizer.adjust_for_ambient_noise(source, duration=1)

            # ✅ Listen for up to 10 seconds, but stop if silent for 5 seconds
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=28)

            try:
                text = recognizer.recognize_google(audio)
                print("🗣️ You said:", text)
                return text
            except sr.UnknownValueError:
                print("🤷 Sorry, I couldn't understand the audio.")
                return "Sorry, I didn't catch that."
            except sr.RequestError as e:
                print("❌ Could not reach speech service:", e)
                return "Speech service is unavailable."

    except OSError as e:
        print("🎤 Microphone not accessible:", e)
        return "Microphone not working. Please check your device."
