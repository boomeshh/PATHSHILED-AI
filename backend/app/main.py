"""
PathShield AI — FastAPI application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routes.reports import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise the database schema on startup."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="PathShield AI", lifespan=lifespan)

# ---------------------------------------------------------------------------
# CORS — allow the Vite dev server to reach the API
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(router)
