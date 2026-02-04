"""FastAPI application entrypoint."""

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI app."""

    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/health")
    def healthcheck() -> dict[str, str]:
        """Return a basic health status."""

        return {"status": "ok"}

    return app


app = create_app()
