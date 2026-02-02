"""
FastAPI application entry point for the Adaptive Coaching Platform.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import chat, voice, image, profile
from app.core.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan handler.
    Handles startup and shutdown events.

    Args:
        app: FastAPI application instance.

    Yields:
        None
    """
    # Startup
    settings = get_settings()

    # Create storage directories if they don't exist
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)
    settings.data_dir.mkdir(parents=True, exist_ok=True)

    yield

    # Shutdown
    pass


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured application instance.
    """
    settings = get_settings()

    app = FastAPI(
        title="Adaptive Adolescent Coaching Platform",
        description="Multi-agent coaching system for nutrition, fitness, and recovery",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(chat.router, prefix="/api", tags=["Chat"])
    app.include_router(voice.router, prefix="/api", tags=["Voice"])
    app.include_router(image.router, prefix="/api", tags=["Image"])
    app.include_router(profile.router, prefix="/api", tags=["Profile"])

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "name": "Adaptive Adolescent Coaching Platform",
            "version": "1.0.0",
            "status": "running"
        }

    @app.get("/health")
    async def health_check():
        """Application health check."""
        return {
            "status": "healthy",
            "services": {
                "chat": "up",
                "voice": "up",
                "image": "up",
                "profile": "up"
            }
        }

    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
