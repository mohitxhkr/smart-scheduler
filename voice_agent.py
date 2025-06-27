import os
import wave
import time
import numpy as np
import whisper
import pygame
import tempfile
import pyaudio
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from llm_engine import generate_response

# Load environment
load_dotenv()
api_key = os.getenv("ELEVENLABS_API_KEY")
voice_id = os.getenv("ELEVENLABS_VOICE_ID")  # Rachel

client = ElevenLabs(api_key=api_key)
model = whisper.load_model("base")

def record_until_silence(threshold=300, silence_limit=0.5, max_duration=3.5, filename="temp_input.wav"):
    print("🎙 Listening (volume threshold-based)...")

    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

    frames = []
    silence_start = None
    recording_start = time.time()

    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)

        audio_data = np.frombuffer(data, dtype=np.int16)
        volume = np.linalg.norm(audio_data)

        current_time = time.time()
        elapsed = current_time - recording_start

        if volume < threshold:
            if silence_start is None:
                silence_start = current_time
            elif current_time - silence_start > silence_limit:
                print("🛑 Detected sustained silence. Stopping recording.")
                break
        else:
            silence_start = None

        if elapsed > max_duration:
            print("⏱️ Max recording time reached. Stopping.")
            break

    stream.stop_stream()
    stream.close()
    p.terminate()

    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

    return filename

def transcribe_audio(audio_path):
    print("📝 Transcribing...")
    result = model.transcribe(audio_path, fp16=False)
    return result["text"]


def synthesize_speech(text, voice_id=voice_id):
    print("🗣️ Synthesizing speech...")
    audio_stream = client.text_to_speech.convert(
        voice_id=voice_id,
        model_id="eleven_monolingual_v1",
        text=text
    )
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        for chunk in audio_stream:
            tmp.write(chunk)
        return tmp.name

def play_audio(file_path):
    print("🔊 Playing...")
    pygame.init()
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        continue
    pygame.quit()

def synthesize_and_speak(text):
    path = synthesize_speech(text)
    play_audio(path)

def run_voice_agent(confirm=True):
    audio_path = record_until_silence()
    user_text = transcribe_audio(audio_path)
    print("👤 You said:", user_text)

    if confirm:
        synthesize_and_speak(f"Did you say: {user_text}? Please say yes or no.")
        confirmation_path = record_until_silence()
        confirmation = transcribe_audio(confirmation_path)

        if "no" in confirmation.lower():
            synthesize_and_speak("Okay, please repeat your message.")
            return run_voice_agent(confirm=True)

    bot_reply = generate_response(user_text)
    print("🤖 Assistant:", bot_reply)
    synthesize_and_speak(bot_reply)

    return user_text, bot_reply

if __name__ == "__main__":
    try:
        print("✅ Voice Agent Starting...")
        run_voice_agent()
        print("✅ Session complete.")
    except Exception as e:
        print("❌ Error running voice agent:", e)