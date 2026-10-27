"""
CyberTrace AI - FastAPI Application Entry Point.
Provides REST API, automated Swagger UI (/docs), CORS, and persistent SQLite DB initialization.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.app.core.config import settings
from backend.app.database.session import init_db, SessionLocal
from backend.app.database.repository import Repository
from backend.app.scenarios.library import build_scenario_library
from backend.app.api.routes import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database tables and seed scenario library
    init_db()
    db = SessionLocal()
    try:
        scenarios = build_scenario_library()
        for s in scenarios:
            Repository.save_scenario(db, s)
    finally:
        db.close()
    yield
    # Shutdown logic if needed


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Deterministic Cyber-Physical EV Charging Simulation & Counterfactual Replay Platform.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for local Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes under /api
app.include_router(api_router, prefix="/api")


@app.get("/")
def root():
    return {
        "service": settings.APP_NAME,
        "tagline": settings.TAGLINE,
        "version": settings.APP_VERSION,
        "mode": "SIMULATION MODE",
        "docs": "/docs",
        "api": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
