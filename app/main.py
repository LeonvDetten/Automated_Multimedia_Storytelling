"""FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import get_settings
from app.web.routes import router as web_router
from app.db.session import ensure_episode_image_urls_column


def create_app() -> FastAPI:
    """Create and configure the FastAPI app."""

    settings = get_settings()
    app = FastAPI(title=settings.app_name)

    @app.on_event("startup")
    def _ensure_schema() -> None:
        # Ensure runtime DB schema compatibility for `image_urls` column.
        ensure_episode_image_urls_column()

    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    app.include_router(web_router)
    app.include_router(api_router, prefix="/api")

    @app.get("/health")
    def healthcheck() -> dict[str, str]:
        """Return a basic health status."""

        return {"status": "ok"}

    return app


app = create_app()
