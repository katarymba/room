"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, room, chat, location
from app.routers import websocket as ws_router
from app.websocket.manager import ConnectionManager

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API for Room — anonymous location-based chat application",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Global WebSocket connection manager (in-memory for MVP)
app.state.ws_manager = ConnectionManager()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(room.router, prefix="/api/room", tags=["Room"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(location.router, prefix="/api/location", tags=["Location"])
app.include_router(ws_router.router, prefix="/ws", tags=["WebSocket"])


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
    }
