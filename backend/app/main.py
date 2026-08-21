import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.config import ALLOWED_ORIGINS
from backend.app.routers import health, trigger, status as status_router, visualization

app = FastAPI(
    title="Environmental Intelligence Pipeline API",
    description="Backend API service connecting Environmental Intelligence ETL, Prefect workflows, PostgreSQL, and React dashboards.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration for local React frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(health.router)
app.include_router(trigger.router)
app.include_router(status_router.router)
app.include_router(visualization.router)


@app.get("/", include_in_schema=False)
def root_redirect():
    """Root endpoint info response."""
    return {
        "title": "Environmental Intelligence Pipeline API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "trigger": "/api/trigger",
        "status": "/api/status/{run_id}",
        "visualization_air_quality": "/api/visualization/air-quality",
        "visualization_earthquakes": "/api/visualization/earthquakes",
        "analytics_trends": "/api/analytics/trends",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
