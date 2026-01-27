"""
RFP Bid Agent - FastAPI Application Entry Point
"""

import sys
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from config.settings import settings
from src.app.core.logging_config import setup_logging, logger
from src.app.core.exceptions import RFPException


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events for the application."""
    # Startup
    setup_logging()
    logger.info(f"🚀 RFP Bid Agent starting... Environment: {settings.ENV}")
    logger.info(f"📊 Log level: {settings.LOG_LEVEL}")
    
    yield
    
    # Shutdown
    logger.info("👋 RFP Bid Agent shutting down...")


# Create FastAPI app instance
app = FastAPI(
    title="RFP Bid Decision Agent",
    description="AI Agent for RFP Bid/No-Bid Decision Support & Compliance Mapping",
    version="1.0.0",
    lifespan=lifespan
)


# CORS Middleware - Allow all in development
if not settings.is_production:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8000", "http://127.0.0.1:8000", "*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Global Exception Handler
@app.exception_handler(RFPException)
async def rfp_exception_handler(request: Request, exc: RFPException):
    """Handle all RFP-related exceptions."""
    logger.error(f"RFP Exception: {exc.message}")
    return JSONResponse(
        status_code=400,
        content={"error": exc.__class__.__name__, "message": exc.message}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    logger.error(f"Unhandled Exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "InternalServerError", "message": "An unexpected error occurred"}
    )


# Import and include routers
# Import and include routers
from src.app.api.routes.health import router as health_router
from src.app.api.routes.recommendation import router as recommendation_router
from src.app.api.routes.outcomes import router as outcome_router
# Knowledge router might not be used by UI yet, but keeping hygiene
from src.app.api.routes.knowledge import router as knowledge_router

app.include_router(health_router, prefix="/api/v1", tags=["Health"])
app.include_router(recommendation_router, prefix="/api/v1/recommendation", tags=["Recommendation"])
app.include_router(outcome_router, prefix="/api/v1/outcomes", tags=["Outcomes"])
app.include_router(knowledge_router, prefix="/api/v1/knowledge", tags=["Knowledge"])


# Serve frontend static files
FRONTEND_DIR = Path(__file__).parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


# Root endpoint - Serve frontend
@app.get("/")
async def root():
    """Serve the frontend UI."""
    frontend_path = FRONTEND_DIR / "index.html"
    if frontend_path.exists():
        return FileResponse(frontend_path)
    return {
        "name": "RFP Bid Decision Agent",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


# API info endpoint
@app.get("/api")
async def api_info():
    """API information endpoint."""
    return {
        "name": "RFP Bid Decision Agent",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=not settings.is_production
    )

