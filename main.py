"""
FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import router
from src.api.websocket_routes import router as websocket_router

app = FastAPI(
    title="AI Workflow Generator",
    description="Generate functional requirements, PRD, time estimates, and cost estimates",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api", tags=["workflow"])
app.include_router(websocket_router, tags=["websocket"])


@app.get("/")
async def root():
    return {"message": "AI Workflow Generator API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

