"""Pytest fixtures for phase 1 API and service tests."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models.character import Character
from app.models.story_series import StorySeries
from app.models.theme import Theme


@pytest.fixture()
def test_session_factory() -> Generator[sessionmaker, None, None]:
    """Create an isolated in-memory SQLite session factory for each test."""

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)
    try:
        yield TestingSessionLocal
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def seeded_db(test_session_factory: sessionmaker) -> Session:
    """Return a database session pre-loaded with one theme, series, and two characters."""

    db = test_session_factory()
    db.add(Theme(key="betrayal", label="Betrayal", description="Trust broken", active=True))
    db.add(StorySeries(title="Default Series", description="For tests", language="en"))
    db.add(
        Character(
            name="Character One",
            speech_style="calm",
            traits_json={"tone": "soft"},
            description="First test character",
            active=True,
        )
    )
    db.add(
        Character(
            name="Character Two",
            speech_style="direct",
            traits_json={"tone": "sharp"},
            description="Second test character",
            active=True,
        )
    )
    db.commit()
    return db


@pytest.fixture()
def client(test_session_factory: sessionmaker) -> Generator[TestClient, None, None]:
    """Create a FastAPI TestClient with DB dependency override."""

    app = create_app()

    def override_get_db() -> Generator[Session, None, None]:
        db = test_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
