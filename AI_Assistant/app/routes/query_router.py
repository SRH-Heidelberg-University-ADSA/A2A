from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from app.services.agent_service import query_llm
from app.tools.delegation_tools import set_file_context, clear_file_context
from app.dependencies import verify_api_key

import logging

# Configure Logging
logger = logging.getLogger("Query_Router")

router = APIRouter(dependencies=[Depends(verify_api_key)])


class QueryRequest(BaseModel):
    query: str
    user_id: Optional[str] = "default"
    file_content_base64: Optional[str] = None
    filename: Optional[str] = None


@router.post("/query")
def handle_query(request: QueryRequest, raw_request: Request = None):
    """
    Unified query endpoint — the A2A coordinator receives all requests
    and delegates to specialized agents.
    """
    logger.info(f"Received query: {request.query}")
    try:
        trace_log = getattr(raw_request.state, "trace", []) if raw_request else []
        
        file_info = None
        if request.file_content_base64:
            set_file_context(request.file_content_base64, request.filename)
            file_info = {"filename": request.filename, "has_data": True}
            logger.info(f"File attached: {request.filename}")
        
        try:
            result = query_llm(request.query, request.user_id, trace_log, file_info=file_info)
        finally:
            clear_file_context()

        if result.get("type") == "response":
            response = result["content"]
        elif result.get("type") == "error":
            response = result.get("content", "An error occurred processing your request.")
        else:
            response = "Unable to process your request."

        return {
            "response": response,
            "enhanced": result.get("enhanced", False),
            "fallback_used": result.get("fallback", False),
            "trace": trace_log,
            "input_tokens": result.get("input_tokens", 0),
            "output_tokens": result.get("output_tokens", 0)
        }

    except Exception as e:
        print(f"Error in query_router: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}.")


@router.get("/agents")
def get_agents():
    """Returns the list of discovered agents for the sidebar."""
    try:
        from app.services.discovery import get_all_agents, fetch_agent_card
        agents = get_all_agents()
        result = []
        for agent in agents:
            card = fetch_agent_card(agent["name"])
            caps = []
            if card and card.get("capabilities"):
                for cap in card["capabilities"]:
                    caps.append({"name": cap.get("name", ""), "description": cap.get("description", "")})
            result.append({
                "name": agent["name"],
                "description": agent.get("description", ""),
                "protocol": agent.get("call_config", {}).get("protocol", "unknown"),
                "capabilities": caps,
            })
        return {"agents": result}
    except Exception as e:
        return {"agents": [], "error": str(e)}
