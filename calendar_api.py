import os
import pytz
from dateutil.parser import isoparse
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/calendar']
IST = pytz.timezone("Asia/Kolkata")

def authenticate_google_calendar():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('calendar', 'v3', credentials=creds)

def get_free_slots(service, duration_minutes, days=7, buffer_minutes=15):
    now = datetime.now(IST)
    end = now + timedelta(days=days)

    events_result = service.events().list(
        calendarId='primary',
        timeMin=now.isoformat(),
        timeMax=end.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    busy_times = [
        (isoparse(e['start']['dateTime']), isoparse(e['end']['dateTime']))
        for e in events if 'dateTime' in e['start']
    ]

    free_slots = []
    current = now + timedelta(minutes=buffer_minutes)
    while current + timedelta(minutes=duration_minutes) <= end:
        overlap = any(
            start <= current < end_time or
            start < current + timedelta(minutes=duration_minutes) <= end_time
            for start, end_time in busy_times
        )
        if not overlap:
            free_slots.append(current.astimezone(IST).isoformat())
        current += timedelta(minutes=30)

    return free_slots

def create_meeting(service, start_time_str, duration_minutes, summary="Smart Scheduler Meeting"):
    try:
        start_time = isoparse(start_time_str)
        if start_time.tzinfo is None:
            start_time = IST.localize(start_time)
        else:
            start_time = start_time.astimezone(IST)

        end_time = start_time + timedelta(minutes=duration_minutes)

        print("📅 Scheduling at IST:", start_time.strftime("%d-%b-%Y %I:%M %p %Z"))

        event = {
            'summary': summary,
            'description': 'Scheduled by your voice assistant.',
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'Asia/Kolkata'
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'Asia/Kolkata'
            },
            'reminders': {
                'useDefault': True
            }
        }

        created_event = service.events().insert(calendarId='primary', body=event).execute()
        print("✅ Event created:", created_event.get('htmlLink'))
        return created_event.get('htmlLink')

    except Exception as e:
        print("❌ Error creating event:", e)
        return None
