import time
import uuid
import logging
import json
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Configure JSON logging
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
        }
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

# Console Handler
c_handler = logging.StreamHandler()
c_handler.setFormatter(JsonFormatter())
logger.addHandler(c_handler)

# File Handler
f_handler = logging.FileHandler("app.json.log")
f_handler.setFormatter(JsonFormatter())
logger.addHandler(f_handler)

class LogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Generate or extract Request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # 2. Add to request state for access in dependencies/routers
        request.state.request_id = request_id
        request.state.trace = [] # Initialize trace collection
        
        # 3. Log Request Entry
        start_time = time.time()
        logger.info(f"Request started: {request.method} {request.url.path}", extra={"request_id": request_id})
        
        try:
            response = await call_next(request)
            
            # 4. Add Request ID to Response Headers
            response.headers["X-Request-ID"] = request_id
            
            # 5. Log Request Exit
            process_time = (time.time() - start_time) * 1000
            logger.info(
                f"Request completed: {response.status_code}", 
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "duration_ms": round(process_time, 2)
                }
            )
            return response
            
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            logger.error(
                f"Request failed: {str(e)}", 
                extra={
                    "request_id": request_id, 
                    "duration_ms": round(process_time, 2)
                },
                exc_info=True
            )
            raise e
