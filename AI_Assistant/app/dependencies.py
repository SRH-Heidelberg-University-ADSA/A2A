from fastapi import Header, HTTPException, Request, Depends
from app.config import Settings
import logging

settings = Settings()
logger = logging.getLogger("app")

async def get_request_id(request: Request) -> str:
    """Dependency to get the request ID from middleware."""
    if hasattr(request.state, "request_id"):
        return request.state.request_id
    # Fallback if middleware didn't run (e.g. tests)
    return "unknown-request-id"

async def verify_api_key(
    request: Request,
    x_api_key: str = Header(..., description="API Key for authentication"),
    request_id: str = Depends(get_request_id)
):
    """
    Verifies the X-API-Key header against the configured APP_API_KEY.
    Logs the attempt with the request_id.
    """
    if not settings.app_api_key:
        # If no key configured, warn but allow (or fail secure - usually fail secure)
        logger.warning("APP_API_KEY not configured! Allowing request (Development Mode).", extra={"request_id": request_id})
        return x_api_key

    if x_api_key != settings.app_api_key:
        logger.warning(f"Invalid API Key attempt: {x_api_key}", extra={"request_id": request_id})
        raise HTTPException(status_code=403, detail="Invalid API Key")
    
    # Trace Success
    if hasattr(request, "state") and hasattr(request.state, "trace"):
        request.state.trace.append("✅ **Authentication**: API Key Verified")
    
    return x_api_key
