from langchain_core.tools import tool
from app.services.google_calendar_service import (
    get_upcoming_events,
    create_event,
    delete_event,
    find_events,
    get_free_slots
)
from datetime import datetime, timedelta
import json

@tool
def list_calendar_events() -> str:
    """
    List the upcoming events on the user's calendar.
    Returns a string summary of events.
    """
    try:
        events = get_upcoming_events()
        if not events:
            return "No upcoming events found."
        
        result = "Upcoming Events:\n"
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            result += f"- {event['summary']} at {start} (ID: {event['id']})\n"
        return result
    except Exception as e:
        return f"Error fetching events: {str(e)}"

@tool
def schedule_calendar_event(summary: str, start_time: str, end_time: str) -> str:
    """
    Schedule a new event on the calendar.
    Args:
        summary: The title or description of the event.
        start_time: Start time in ISO format (e.g., '2023-10-27T10:00:00') or specific format.
        end_time: End time in ISO format.
    """
    try:
        # Basic validation/formatting could happen here if needed, 
        # but we rely on the LLM to provide valid ISO strings or the service to handle it.
        event_id = create_event(summary, start_time, end_time)
        return f"Event '{summary}' scheduled successfully with ID: {event_id}"
    except Exception as e:
        return f"Error scheduling event: {str(e)}"

@tool
def delete_calendar_event(event_id: str) -> str:
    """
    Delete a calendar event by its ID.
    Args:
        event_id: The unique identifier of the event to delete.
    """
    try:
        delete_event(event_id)
        return "Event deleted successfully."
    except Exception as e:
        return f"Error deleting event: {str(e)}"

@tool
def find_and_delete_event(query: str) -> str:
    """
    Find an event by name/query and delete it. 
    Useful when the user asks to 'cancel meeting with X' but doesn't provide an ID.
    """
    try:
        matches = find_events(query)
        if not matches:
            return f"No events found matching '{query}'."
        
        if len(matches) == 1:
            event = matches[0]
            delete_event(event['id'])
            return f"Cancelled event '{event['summary']}'."
        
        # Multiple matches
        summary = "Found multiple events. Please specify which one to delete by ID or be more specific:\n"
        for e in matches:
            start = e['start'].get('dateTime', e['start'].get('date'))
            summary += f"- {e['summary']} at {start} (ID: {e['id']})\n"
        return summary
    except Exception as e:
        return f"Error cancelling event: {str(e)}"

@tool
def get_available_slots(duration_minutes: int = 60, days_ahead: int = 3) -> str:
    """
    Find free time slots in the calendar.
    Args:
        duration_minutes: Length of the slot in minutes.
        days_ahead: How many days to look ahead.
    """
    try:
        slots = get_free_slots(duration_minutes, days_ahead)
        if not slots:
            return "No free slots found."
        
        result = f"Available {duration_minutes}-minute slots:\n"
        for slot in slots[:10]: # Limit to 10
            result += f"- {slot['start']} to {slot['end']}\n"
        return result
    except Exception as e:
        return f"Error finding slots: {str(e)}"
