import os
import uvicorn
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional

# Import the brain we just built!
from agent import answer_question

app = FastAPI(title="Krishi-Intel Pro API", version="1.0")

# ==========================================
# 1. SECURITY SETUP
# ==========================================
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    expected_token = os.environ.get("API_BEARER_TOKEN", "krishi-secret-123")
    if credentials.credentials != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Bearer Token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

# ==========================================
# 2. FLEXIBLE API STRATEGY (Pydantic Models)
# ==========================================
class ChatRequest(BaseModel):
    message: Optional[str] = None
    query:   Optional[str] = None
    text:    Optional[str] = None

# ==========================================
# 3. TOKEN COUNTING
# Works with ANY provider including OpenRouter/Gemini
# Counts question + ALL tool results + final answer
# Much more accurate than just question+answer
# ==========================================
def count_tokens_from_steps(user_input: str, result: dict) -> dict:
    """
    Count tokens from the full agent run:
    - user question
    - all intermediate tool results  <- THIS is what was missing before
    - final answer
    1 token = 4 characters (standard approximation)
    """
    total_text = user_input  # start with question

    # add ALL tool call results
    # Tavily search, weather data, soil data all add many tokens
    for step in result.get("intermediate_steps", []):
        if isinstance(step, list) and len(step) > 1:
            total_text += str(step[1])

    # add final answer
    total_text += result.get("output", "")

    total_tokens      = max(1, len(total_text) // 4)
    prompt_tokens     = int(total_tokens * 0.75)
    completion_tokens = total_tokens - prompt_tokens

    return {
        "total_tokens":      total_tokens,
        "prompt_tokens":     prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_cost_usd":    round(total_tokens * 0.000001, 6)
    }

# ==========================================
# 4. PUBLIC DISCOVERY ENDPOINTS (A2A Protocol)
# ==========================================
AGENT_CARD_PATH = os.path.join("static", ".well-known", "agent.json")  # ADRESS FOR JSON  file 

@app.get("/.well-known/agent.json")
def get_agent_card():
    if os.path.exists(AGENT_CARD_PATH):
        return FileResponse(AGENT_CARD_PATH)
    return {
        "name": "Krishi-Intel Pro",
        "description": "Expert Agricultural AI Assistant",
        "endpoints": [{"path": "/chat", "method": "POST"}]
    }

@app.get("/agent.json")
def get_agent_card_backup():
    return get_agent_card()


@app.post("/chat")   # door wherre question is sent
async def chat(req: ChatRequest, token: str = Depends(verify_token)):   # recive question and  checks whether token correct
    user_input = req.message or req.query or req.text

    if not user_input:
        return {
            "error": "I couldn't understand your request format.",
            "hint": "Please send your JSON payload with the key 'message', 'query', or 'text'."
        }

    # Run agent normally — no wrapper that breaks async
    result = await answer_question(user_input)   # calling agent to answer question 

    # Count tokens from full run including all tool results
    token_info = count_tokens_from_steps(user_input, result)

    return {
        "output":             result["output"],
        "intermediate_steps": result.get("intermediate_steps", []),
        "total_tokens":       token_info["total_tokens"],
        "prompt_tokens":      token_info["prompt_tokens"],
        "completion_tokens":  token_info["completion_tokens"],
        "total_cost_usd":     token_info["total_cost_usd"]
    }