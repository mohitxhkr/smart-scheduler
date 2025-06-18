import re
import pytz
import dateparser
from datetime import datetime
from voice_input import listen
from voice_output import speak
from dateutil.parser import isoparse
from llm_engine import generate_response
from calendar_api import authenticate_google_calendar, get_free_slots, create_meeting

IST = pytz.timezone("Asia/Kolkata")

def parse_datetime_from_text(text):
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
        speak("You have no upcoming meetings.")
        return

    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        summary = event.get('summary', 'No title')
        time_obj = isoparse(start).astimezone(IST)
        formatted_time = time_obj.strftime("%d %B, %Y at %I:%M %p")
        speak(f"{summary} on {formatted_time}")
        print(f"{summary} on {formatted_time}")

def main():
    speak("Hi! I’m your Smart Scheduler assistant. How can I help you today?")

    calendar_service = authenticate_google_calendar()
    conversation_context = ""

    while True:
        speak("I'm listening...")
        user_input = listen()
        print("User:", user_input)

        if "stop" in user_input.lower() or "exit" in user_input.lower():
            speak("Okay, ending the session. Goodbye!")
            break

        if "show" in user_input.lower() and "schedule" in user_input.lower():
            list_events(calendar_service)
            continue

        conversation_context += f"\nUser: {user_input}"

        try:
            bot_reply = generate_response(user_input)
        except Exception as e:
            speak("There was a problem with the language model.")
            print("❌ LLM error:", e)
            continue

        print("Bot:", bot_reply)
        speak(bot_reply)
        conversation_context += f"\nAssistant: {bot_reply}"

        # Parse the time from user input or LLM reply
        scheduled_time = parse_datetime_from_text(user_input) or parse_datetime_from_text(bot_reply)

        if scheduled_time:
            formatted = scheduled_time.strftime("%d %B, %Y at %I:%M %p")
            speak(f"Should I schedule the meeting on {formatted}?")
            confirm = listen().lower()
            if any(word in confirm for word in ["yes", "sure", "okay", "go ahead"]):
                speak("What should be the meeting title?")
                meeting_title = listen()

                speak("How long should the meeting be? You can say things like '1 hour', or '30 minutes'.")
                duration_input = listen().lower()
                print("⏱️ Duration input:", duration_input)

                # Default
                duration = 60

                # Extract numbers and context
                hours = re.search(r"(\d+)\s*hour", duration_input)
                minutes = re.search(r"(\d+)\s*minute", duration_input)

                if hours and minutes:
                    duration = int(hours.group(1)) * 60 + int(minutes.group(1))
                elif hours:
                    duration = int(hours.group(1)) * 60
                elif minutes:
                    duration = int(minutes.group(1))
                else:
                    # Try fallback: look for any number if no keyword
                    match = re.search(r"\d+", duration_input)
                    duration = int(match.group()) if match else 60

                print(f"🕒 Final meeting duration: {duration} minutes")

                try:
                    link = create_meeting(calendar_service, scheduled_time.isoformat(), duration, summary=meeting_title)
                    speak("Your meeting has been scheduled. Here is the link.")
                    print("📅 Meeting link:", link)
                    conversation_context = ""
                    break
                except Exception as e:
                    speak("There was a problem creating the meeting.")
                    print("❌ Calendar error:", e)
            else:
                speak("Okay, I won’t schedule it yet.")
                conversation_context = ""
        else:
            speak("I didn't catch the meeting time. Could you please say it again?")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("❌ Error occurred in main:", e)
    except KeyboardInterrupt:
        print("\n👋 Goodbye! Exiting the Smart Scheduler.")
        speak("Goodbye! Have a great day!")
