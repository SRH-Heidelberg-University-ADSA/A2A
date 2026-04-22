from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from app.services.google_calendar_service import (
    get_upcoming_events,
    get_free_slots,
    create_event,
    delete_event
)

router = APIRouter()


@router.get("/calendar/events")
def get_events():
    """Get upcoming calendar events."""
    try:
        events = get_upcoming_events()
        return {"success": True, "data": events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch events: {str(e)}")


@router.get("/calendar/free-slots")
def get_free_slots_route(
    duration_minutes: int = Query(60, description="Duration in minutes"),
    days_ahead: int = Query(7, description="Days to look ahead")
):
    """Get free time slots."""
    try:
        slots = get_free_slots(duration_minutes, days_ahead)
        return {"success": True, "data": slots}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find free slots: {str(e)}")


class CreateEventRequest(BaseModel):
    summary: str
    start_time: str  # ISO format
    end_time: str


@router.post("/calendar/create")
def create_calendar_event(request: CreateEventRequest):
    """Create a new calendar event."""
    try:
        event_id = create_event(request.summary, request.start_time, request.end_time)
        return {"success": True, "event_id": event_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to schedule event: {str(e)}")


@router.delete("/calendar/delete/{event_id}")
def delete_calendar_event(event_id: str):
    """Delete a calendar event by ID."""
    try:
        delete_event(event_id)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete event: {str(e)}")
