import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pygame.pkgdata")
import re
import pytz
import dateparser
from datetime import datetime
from dateutil.parser import isoparse
from dotenv import load_dotenv

from voice_agent import run_voice_agent, synthesize_speech, play_audio, synthesize_and_speak
from llm_engine import generate_response
from calendar_api import authenticate_google_calendar, get_free_slots, create_meeting

# Load environment variables
load_dotenv()

IST = pytz.timezone("Asia/Kolkata")

def parse_datetime_from_text(text):
    if not text:
        return None

    full_pattern = r"(\d{1,2}(?:st|nd|rd|th)?\s+\w+,\s*\d{4}).*?(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))"
    match = re.search(full_pattern, text)
    if match:
        date_str = match.group(1)
        time_str = match.group(2)
        full_str = f"{date_str} {time_str}"
        print(f"📅 Extracted datetime string: {full_str}")
        parsed = dateparser.parse(
            full_str,
            settings={
                'TIMEZONE': 'Asia/Kolkata',
                'RETURN_AS_TIMEZONE_AWARE': True,
                'PREFER_DATES_FROM': 'future'
            }
        )
        return parsed

    general_parsed = dateparser.parse(
        text,
        settings={
            'TIMEZONE': 'Asia/Kolkata',
            'RETURN_AS_TIMEZONE_AWARE': True,
            'PREFER_DATES_FROM': 'future'
        }
    )
    if general_parsed:
        print(f"📅 General parsed datetime: {general_parsed}")
        return general_parsed

    return None

def list_events(service):
    print("\n📆 Your upcoming meetings:")
    events_result = service.events().list(
        calendarId='primary',
        maxResults=5,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    if not events:
        print("No upcoming events found.")
        synthesize_and_speak("You have no upcoming meetings.")
        return

    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        summary = event.get('summary', 'No title')
        time_obj = isoparse(start).astimezone(IST)
        formatted_time = time_obj.strftime("%d %B, %Y at %I:%M %p")
        synthesize_and_speak(f"{summary} on {formatted_time}")
        print(f"{summary} on {formatted_time}")

def main():
    synthesize_and_speak("Hi! I’m your Smart Scheduler assistant. How can I help you today?")

    calendar_service = authenticate_google_calendar()
    conversation_context = ""

    while True:
        synthesize_and_speak("I'm listening...")
        try:
            result = run_voice_agent()
            if not result or not isinstance(result, tuple) or len(result) < 2:
                synthesize_and_speak("Sorry, I didn't catch that. Please try again.")
                continue

            user_input, bot_reply = result
        except Exception as e:
            print("❌ Voice Agent Error:", e)
            synthesize_and_speak("Sorry, something went wrong.")
            continue

        print("User:", user_input)

        if not user_input:
            synthesize_and_speak("Sorry, I didn't hear anything.")
            continue

        if "stop" in user_input.lower() or "exit" in user_input.lower():
            synthesize_and_speak("Okay, ending the session. Goodbye!")
            break

        if "show" in user_input.lower() and "schedule" in user_input.lower():
            list_events(calendar_service)
            continue

        conversation_context += f"\nUser: {user_input}\nAssistant: {bot_reply}"

        scheduled_time = None
        if user_input:
            scheduled_time = parse_datetime_from_text(user_input)
        if not scheduled_time and bot_reply:
            scheduled_time = parse_datetime_from_text(bot_reply)

        if scheduled_time:
            formatted = scheduled_time.strftime("%d %B, %Y at %I:%M %p")
            synthesize_and_speak(f"Should I schedule the meeting on {formatted}?")
            confirm_result = run_voice_agent()
            confirm_input = confirm_result[0] if confirm_result and isinstance(confirm_result, tuple) else ""

            if any(word in confirm_input.lower() for word in ["yes", "sure", "okay", "go ahead"]):
                synthesize_and_speak("What should be the meeting title?")
                title_result = run_voice_agent()
                title = title_result[0] if title_result and isinstance(title_result, tuple) else "Untitled Meeting"

                synthesize_and_speak("How long should the meeting be? You can say things like '1 hour' or '30 minutes'.")
                duration_result = run_voice_agent()
                duration_input = duration_result[0] if duration_result and isinstance(duration_result, tuple) else "60"

                print("⏱️ Duration input:", duration_input)

                duration = 60  # Default

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

                print(f"🕒 Final meeting duration: {duration} minutes")

                try:
                    link = create_meeting(
                        calendar_service,
                        scheduled_time.isoformat(),
                        duration,
                        summary=title
                    )
                    synthesize_and_speak("Your meeting has been scheduled. Here is the link.")
                    print("📅 Meeting link:", link)
                    conversation_context = ""
                except Exception as e:
                    print("❌ Calendar error:", e)
                    synthesize_and_speak("There was a problem creating the meeting.")
            else:
                synthesize_and_speak("Okay, I won’t schedule it yet.")
                conversation_context = ""
        else:
            synthesize_and_speak("I didn't catch the meeting time. Could you please say it again?")

if __name__ == "__main__":
    try:
        print("✅ Starting Smart Scheduler")
        main()
    except KeyboardInterrupt:
        print("\n👋 Goodbye! Exiting the Smart Scheduler.")
        synthesize_and_speak("Goodbye! Have a great day!")
    except Exception as e:
        print("❌ Error occurred in main:", e)
