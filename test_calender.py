from calendar_api import authenticate_google_calendar, create_meeting
from datetime import datetime, timedelta
import pytz

service = authenticate_google_calendar()

# Schedule 2 hours from now in IST
ist = pytz.timezone("Asia/Kolkata")
start = ist.localize(datetime.now() + timedelta(hours=2))
start_iso = start.isoformat()

link = create_meeting(service, start_iso, 30, summary="Test Meeting via Script")
print("📅 Meeting link:", link)
