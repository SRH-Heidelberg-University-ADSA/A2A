from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import uvicorn
import os
from typing import Optional
import time

# 👇 Import your existing brains 
from agents.guardrail_bot import validate_topic
from agents.rules_bot import get_official_ruling
from agents.content_bot import create_social_post

app = FastAPI(title="Football Content Agent API")

# Define the "Data Model" (What other agents must send us)
class EventRequest(BaseModel):
    event_description: str
    persona: str = "hype_man" # Default to Hype Man if they don't ask

# Define the Security Token (Simple Password)
API_SECRET = "GOAL_2026"

@app.post("/generate-tweet")
async def generate_tweet(request: EventRequest, x_auth_token: Optional[str] = Header(None)):
    """
    1. Check Auth
    2. Check Guardrail
    3. Check Rules
    4. Generate Tweet
    """
    # 🔐 1. Security Check
    if x_auth_token != API_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized: Wrong Token")

    print(f"Incoming Request: {request.event_description}")

    # 🛡️ 2. Guardrail Check
    is_allowed, reason = validate_topic(request.event_description)
    if not is_allowed:
        return {
            "status": "blocked",
            "reason": reason,
            "tweet": None
        }
    
    print("⏳ Sleeping for 3 seconds to protect Gemini API limits...")
    time.sleep(20)

    # 🔍 3. Rules Check (Internal Orchestration)
    official_ruling = get_official_ruling(request.event_description)

    print("⏳ Sleeping for 3 seconds to protect Gemini API limits...")
    time.sleep(20)

    # ✍️ 4. Content Generation
    # uses the persona requested by the other agent
    #tweet = create_social_post(request.event_description, official_ruling, request.persona)

    return {
        "status": "success",
        "ruling": official_ruling,
        #"tweet": tweet,
        #"persona_used": request.persona
    }

if __name__ == "__main__":
    # Run on Port 8001 
    uvicorn.run(app, host="0.0.0.0", port=8080)
    