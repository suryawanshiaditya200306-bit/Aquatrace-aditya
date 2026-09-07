from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import (
    ais,
    correlation,
    health,
    predict,
    risk,
    spill,
    status,
    trajectory,
    vessels,
)

app = FastAPI(
    title="AquaSlick API",
    description="Backend for oil-spill detection and water monitoring (prototype).",
    version="0.1.0",
)

# Allow Streamlit (and local browsers) to call this API during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(status.router)
app.include_router(predict.router)
app.include_router(spill.router)
app.include_router(ais.router)
app.include_router(vessels.router)
app.include_router(trajectory.router)
app.include_router(correlation.router)
app.include_router(risk.router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "AquaSlick backend is running!",
        "docs": "/docs",
        "health": "/health",
    }
