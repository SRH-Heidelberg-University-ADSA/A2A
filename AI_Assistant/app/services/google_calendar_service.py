from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from app.config import Settings, CALENDAR_SCOPE
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

settings = Settings()


def get_credentials():
    """Get Google OAuth credentials from stored tokens."""
    creds = Credentials(
        token=settings.google_access_token,
        refresh_token=settings.google_refresh_token,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=[CALENDAR_SCOPE]
    )
    # Handle token refresh if expired
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds


def get_upcoming_events():
    """Fetch upcoming calendar events."""
    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)
    
    tz = ZoneInfo(settings.calendar_timezone)
    now = datetime.now(tz).isoformat()
    
    events_result = service.events().list(
        calendarId='primary', timeMin=now, maxResults=10,
        singleEvents=True, orderBy='startTime'
    ).execute()
    return events_result.get('items', [])


def get_free_slots(duration_minutes=60, days_ahead=7, day=""):
    """Identify free time slots in the upcoming days."""
    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)
    
    tz = ZoneInfo(settings.calendar_timezone)

    # Get busy times
    # Start from 9 AM today in the configured timezone
    now_local = datetime.now(tz).replace(hour=9, minute=0, second=0, microsecond=0)

    if day:
        weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        wd_index = weekdays.index(day.lower()) if day.lower() in weekdays else None
        if wd_index is not None:
            current_wd = datetime.now(tz).weekday()
            days_to_add = (wd_index - current_wd) % 7
            # If days_to_add is 0, it means today is the requested day. We keep it as 0 to include today.
            now_local = (datetime.now(tz) + timedelta(days=days_to_add)).replace(hour=9, minute=0, second=0, microsecond=0)
            days_ahead = 1

    week_later = now_local + timedelta(days=days_ahead)

    body = {
        "timeMin": now_local.isoformat(),
        "timeMax": week_later.isoformat(),
        "timeZone": settings.calendar_timezone,
        "items": [{"id": 'primary'}]
    }

    freebusy_result = service.freebusy().query(body=body).execute()
    busy_periods = freebusy_result['calendars']['primary']['busy']

    # Simple logic: find gaps between 9am-6pm each day
    free_slots = []
    for day_offset in range(days_ahead):
        day_start = now_local + timedelta(days=day_offset)
        day_end = day_start + timedelta(hours=9)  # 9am + 9 hours = 6pm

        # Adjust current_start to be at least now (if today) or 9am (if future day)
        current_time = datetime.now(tz)
        if day_start.date() == current_time.date():
             # Round up to the next hour/interval if needed, or just start from now
             # For simplicity, let's start from the next full interval if we want strict slots,
             # or just use 'now' and let the loop handle it.
             # Let's stick to 'now' but maybe align to minutes?
             current_start = max(day_start, current_time)
        else:
             current_start = day_start
             
        current_end = day_end

        if current_start < current_end:
            # Iterate in chunks of duration_minutes
            slot_start = current_start
            while slot_start + timedelta(minutes=duration_minutes) <= current_end:
                slot_end = slot_start + timedelta(minutes=duration_minutes)
                
                # Check if this slot overlaps with ANY busy period
                is_busy = False
                for busy in busy_periods:
                    # Busy times are usually in UTC or the calendar's timezone. 
                    # The API returns them as ISO strings. We should parse them.
                    busy_start = datetime.fromisoformat(busy['start'].replace('Z', '+00:00'))
                    busy_end = datetime.fromisoformat(busy['end'].replace('Z', '+00:00'))
                    
                    # Convert busy times to our local timezone for comparison
                    busy_start = busy_start.astimezone(tz)
                    busy_end = busy_end.astimezone(tz)

                    # Check overlap: (StartA < EndB) and (EndA > StartB)
                    if slot_start < busy_end and slot_end > busy_start:
                        is_busy = True
                        break
                
                if not is_busy:
                    free_slots.append({
                        'start': slot_start.isoformat(),
                        'end': slot_end.isoformat()
                    })
                
                # Move to next slot. 
                # We can either jump by duration (non-overlapping slots) or by a smaller step (overlapping candidates).
                # User asked for "1 hr duration", usually implies discrete slots.
                slot_start += timedelta(minutes=duration_minutes)

    return free_slots


def ensure_timezone(dt_str):
    """Ensure the datetime string has a timezone offset."""
    tz = ZoneInfo(settings.calendar_timezone)
    try:
        dt = datetime.fromisoformat(dt_str)
    except ValueError:
        # Handle cases where 'Z' might be missing or format is slightly off
        # For simplicity, assume ISO format
        dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
        
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)
    return dt.isoformat()


def check_overlap(start_time, end_time):
    """Check if there are any events overlapping with the given time range."""
    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)
    
    start_iso = ensure_timezone(start_time)
    end_iso = ensure_timezone(end_time)
    
    events_result = service.events().list(
        calendarId='primary', 
        timeMin=start_iso, 
        timeMax=end_iso,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    events = events_result.get('items', [])
    return len(events) > 0


def create_event(summary, start_time, end_time):
    """Create a new calendar event."""
    
    # Ensure inputs are timezone-aware
    start_iso = ensure_timezone(start_time)
    end_iso = ensure_timezone(end_time)
    
    # Check for overlaps
    if check_overlap(start_iso, end_iso):
        raise ValueError("Time slot is already booked.")

    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)

    event = {
        'summary': summary,
        'start': {'dateTime': start_iso, 'timeZone': settings.calendar_timezone},
        'end': {'dateTime': end_iso, 'timeZone': settings.calendar_timezone},
    }
    
    print(f"DEBUG: Creating event: {event}")

    created_event = service.events().insert(calendarId='primary', body=event).execute()
    return created_event['id']


def delete_event(event_id):
    """Delete a calendar event by ID."""
    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)
    service.events().delete(calendarId='primary', eventId=event_id).execute()
    return True


def find_events(query):
    """Find upcoming events that match the query string."""
    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)
    
    # Get upcoming events
    now = datetime.utcnow().isoformat() + 'Z'
    events_result = service.events().list(
        calendarId='primary', timeMin=now,
        maxResults=50, singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])
    
    matches = []
    query_lower = query.lower()
    
    for event in events:
        summary = event.get('summary', '').lower()
        if query_lower in summary:
            matches.append(event)
            
    return matches
