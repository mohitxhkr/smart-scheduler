import speech_recognition as sr

def listen():
    recognizer = sr.Recognizer()

    # 🔧 Make recognizer more sensitive
    recognizer.energy_threshold = 250  # Lower for quiet voices
    recognizer.pause_threshold = 1.0   # Wait longer after pauses
    recognizer.phrase_threshold = 0.5  # Delay before it starts processing
    recognizer.dynamic_energy_threshold = True  # Auto-adjust to environment

    try:
        with sr.Microphone() as source:
            print("🎙️ Adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=1.5)

            print("🎧 Listening (you can speak now)...")
            audio = recognizer.listen(source, timeout=None, phrase_time_limit=60)

            print("🔍 Recognizing...")
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
