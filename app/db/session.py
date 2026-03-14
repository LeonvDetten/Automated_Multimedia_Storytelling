"""Database engine and session helpers."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import inspect, text

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session for request-scoped usage."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_episode_image_urls_column() -> None:
    """Ensure the `image_urls` column exists on the `episodes` table.

    This is a lightweight runtime fix for deployments where Alembic migrations
    have not yet been applied. It will ALTER the table adding a TEXT column
    if it is missing. It's safe to call on startup.
    """

    try:
        inspector = inspect(engine)
        if "episodes" in inspector.get_table_names():
            cols = [c["name"] for c in inspector.get_columns("episodes")]
            if "image_urls" not in cols:
                with engine.begin() as conn:
                    conn.execute(text("ALTER TABLE episodes ADD COLUMN image_urls TEXT"))
    except Exception:
        # If anything goes wrong, don't crash the app startup; migrations should be run manually.
        return
