from voice_input import listen
from voice_output import speak
from llm_engine import generate_response
from calendar_api import authenticate_google_calendar, get_free_slots, create_meeting
import re
import dateparser
from datetime import datetime
import pytz
from dateutil.parser import isoparse

IST = pytz.timezone("Asia/Kolkata")

def parse_datetime_from_text(text):
    full_pattern = r"(\d{1,2}(?:st|nd|rd|th)?\s+\w+,\s*\d{4}).*?(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))"
    match = re.search(full_pattern, text)
    if match:
        date_str = match.group(1)
        time_str = match.group(2)
        full_str = f"{date_str} {time_str}"
        print(f"Extracted datetime string: {full_str}")
        parsed = dateparser.parse(
            full_str,
            settings={
                'TIMEZONE': 'Asia/Kolkata',
                'RETURN_AS_TIMEZONE_AWARE': True
            }
        )
        return parsed

    general_parsed = dateparser.parse(
        text,
        settings={
            'TIMEZONE': 'Asia/Kolkata',
            'RETURN_AS_TIMEZONE_AWARE': True
        }
    )
    if general_parsed:
        print(f"General parsed datetime: {general_parsed}")
        return general_parsed

    return None

def list_events(service):
    print("\n\U0001F4C5 Your upcoming meetings:")
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
            print(e)
            continue

        print("Bot:", bot_reply)
        speak(bot_reply)
        conversation_context += f"\nAssistant: {bot_reply}"

        scheduled_time = parse_datetime_from_text(user_input) or parse_datetime_from_text(bot_reply)

        if scheduled_time:
            formatted = scheduled_time.strftime("%d %B, %Y at %I:%M %p")
            speak(f"Should I schedule the meeting on {formatted}?")
            confirm = listen().lower()
            if any(word in confirm for word in ["yes", "sure", "okay", "go ahead"]):
                speak("What should be the meeting title?")
                meeting_title = listen()

                speak("How long should the meeting be in minutes?")
                duration_input = listen()
                match = re.search(r"\d+", duration_input)
                duration = int(match.group()) if match else 60

                try:
                    link = create_meeting(calendar_service, scheduled_time.isoformat(), duration, summary=meeting_title)
                    speak("Your meeting has been scheduled. Here is the link.")
                    print("\U0001F4C5 Meeting link:", link)
                    speak(link)
                    conversation_context = ""
                    break
                except Exception as e:
                    speak("There was a problem creating the meeting.")
                    print(e)
            else:
                speak("Okay, I won’t schedule it yet.")
                conversation_context = ""
        else:
            speak("Sorry, I couldn't understand the date and time. Please say it again like '17th June, 2025 at 4 PM' or 'tomorrow at 3 PM'.")

        if "book" in user_input.lower() or "schedule" in user_input.lower():
            slots = get_free_slots(calendar_service, 60)
            if slots:
                first_slot = slots[0]
                dt = isoparse(first_slot).astimezone(IST)
                readable = dt.strftime("%d %B, %Y at %I:%M %p")
                speak(f"You have a free slot on {readable}. Should I book it?")
                confirm = listen().lower()
                if "yes" in confirm:
                    link = create_meeting(calendar_service, first_slot, 60)
                    speak("Meeting booked successfully.")
                    print("\U0001F4C5 Meeting link:", link)
                    speak(link)
                    conversation_context = ""
                    break
            else:
                speak("I couldn't find a free slot. Want to try a different time?")

if __name__ == "__main__":
    main()
