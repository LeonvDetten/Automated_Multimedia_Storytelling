"""Phase 1 API router registration."""

from fastapi import APIRouter

from app.api.characters import router as characters_router
from app.api.episodes import router as episodes_router
from app.api.jobs import router as jobs_router
from app.api.series import router as series_router
from app.api.themes import router as themes_router

api_router = APIRouter()
api_router.include_router(themes_router)
api_router.include_router(characters_router)
api_router.include_router(series_router)
api_router.include_router(episodes_router)
api_router.include_router(jobs_router)
