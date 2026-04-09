"""
DischargeIQ API — Main Application

FastAPI application with CORS, PHI filter middleware, and all route modules.
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api.middleware.phi_filter import PHIFilterMiddleware
from src.api.routes.dashboard import router as dashboard_router
from src.api.routes.patients import router as patients_router
from src.api.routes.workflows import router as workflows_router

load_dotenv()

# Configure logging — never log PHI
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="DischargeIQ API",
    version="1.0.0",
    description="Hospital discharge coordination API — HIPAA compliant",
)

# CORS — allow local frontend dev server
_allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# PHI filter middleware — adds Cache-Control: no-store on PHI endpoints
app.add_middleware(PHIFilterMiddleware)

# Include routers
app.include_router(workflows_router)
app.include_router(patients_router)
app.include_router(dashboard_router)


@app.get("/api/health", tags=["health"])
async def health_check():
    """Health check endpoint — no authentication required."""
    return {
        "status": "healthy",
        "service": "DischargeIQ API",
        "version": "1.0.0",
    }


# Serve React frontend static build (Docker production mode)
_static_dir = Path(__file__).resolve().parent.parent.parent / "static"
if _static_dir.is_dir():
    from fastapi.responses import FileResponse

    app.mount("/static", StaticFiles(directory=str(_static_dir / "static")), name="react-static")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        """Serve React SPA — all non-API routes fall through to index.html."""
        file_path = _static_dir / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(_static_dir / "index.html"))


logger.info("DischargeIQ API initialized")
