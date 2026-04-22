from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load explicitly to inject .env vars into os.environ for RPC fallback gets
load_dotenv()

from app.routes import query_router, calendar_routes

# Initialize FastAPI app
app = FastAPI(
    title="A2A Coordinator",
    description="An A2A coordinator that routes requests to specialized agents.",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Logging Middleware
from app.middleware import LogMiddleware
app.add_middleware(LogMiddleware)

# Include API routers
app.include_router(query_router.router, prefix="/api", tags=["Query"])
app.include_router(calendar_routes.router, prefix="/api", tags=["Calendar"])

# Root endpoint
@app.get("/")
async def read_root():
    return {"message": "Welcome to the A2A Coordinator API", "version": "2.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
