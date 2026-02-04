"""Phase 1 tests for API flow and seed idempotency."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.models.character import Character
from app.models.theme import Theme
from scripts import seed as seed_script


def _seed_api_catalog(client) -> tuple[int, int, list[int]]:
    """Create a minimal catalog through API calls and return ids."""

    payload = {
        "name": "Rhea Storm",
        "speech_style": "Measured",
        "traits_json": {"role": "captain"},
        "description": "Leads difficult decisions.",
        "active": True,
    }
    r1 = client.post("/api/v1/characters", json=payload)
    assert r1.status_code == 201
    c1 = r1.json()["id"]

    payload["name"] = "Kade Flint"
    r2 = client.post("/api/v1/characters", json=payload)
    assert r2.status_code == 201
    c2 = r2.json()["id"]

    theme_resp = client.get("/api/v1/themes")
    assert theme_resp.status_code == 200
    theme_id = theme_resp.json()[0]["id"]

    series_resp = client.get("/api/v1/series")
    assert series_resp.status_code == 200
    series_id = series_resp.json()[0]["id"]

    return theme_id, series_id, [c1, c2]


def test_episode_creation_with_valid_theme_and_characters(client, seeded_db: Session) -> None:
    """Episode creation succeeds when theme and characters exist."""

    theme_id, series_id, character_ids = _seed_api_catalog(client)
    response = client.post(
        "/api/v1/episodes",
        json={
            "user_prompt": "A difficult alliance forms at sea.",
            "theme_id": theme_id,
            "series_id": series_id,
            "character_ids": character_ids,
            "target_duration_sec": 15,
            "title": "Storm Pact",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["episode_id"] > 0
    assert payload["job_id"] > 0


def test_episode_creation_without_characters(client, seeded_db: Session) -> None:
    """Episode creation works even when no characters are selected."""

    theme_id, series_id, _ = _seed_api_catalog(client)
    response = client.post(
        "/api/v1/episodes",
        json={
            "user_prompt": "A lone traveler enters a silent city.",
            "theme_id": theme_id,
            "series_id": series_id,
            "character_ids": [],
        },
    )

    assert response.status_code == 201


def test_valid_continuation_reference(client, seeded_db: Session) -> None:
    """Continuation succeeds when previous episode exists."""

    theme_id, series_id, character_ids = _seed_api_catalog(client)
    first = client.post(
        "/api/v1/episodes",
        json={
            "user_prompt": "Part one.",
            "theme_id": theme_id,
            "series_id": series_id,
            "character_ids": character_ids,
        },
    )
    first_episode_id = first.json()["episode_id"]

    second = client.post(
        "/api/v1/episodes",
        json={
            "user_prompt": "Part two.",
            "theme_id": theme_id,
            "series_id": series_id,
            "character_ids": character_ids,
            "continuation_from_episode_id": first_episode_id,
        },
    )

    assert second.status_code == 201


def test_invalid_continuation_reference(client, seeded_db: Session) -> None:
    """Continuation fails when referenced episode is missing."""

    theme_id, series_id, character_ids = _seed_api_catalog(client)
    response = client.post(
        "/api/v1/episodes",
        json={
            "user_prompt": "Part two.",
            "theme_id": theme_id,
            "series_id": series_id,
            "character_ids": character_ids,
            "continuation_from_episode_id": 9999,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Continuation episode not found"


def test_job_status_endpoint_consistent(client, seeded_db: Session) -> None:
    """Job endpoint returns valid status fields after creation."""

    theme_id, series_id, character_ids = _seed_api_catalog(client)
    create_response = client.post(
        "/api/v1/episodes",
        json={
            "user_prompt": "Track this job.",
            "theme_id": theme_id,
            "series_id": series_id,
            "character_ids": character_ids,
        },
    )
    job_id = create_response.json()["job_id"]

    status_response = client.get(f"/api/v1/jobs/{job_id}")
    assert status_response.status_code == 200
    payload = status_response.json()
    assert payload["status"] in {"queued", "running", "completed"}
    assert 0 <= payload["progress_pct"] <= 100
    assert payload["step"]


def test_seed_script_is_idempotent(test_session_factory: sessionmaker, monkeypatch) -> None:
    """Running seed twice should not duplicate fixed themes."""

    monkeypatch.setattr(seed_script, "SessionLocal", test_session_factory)

    seed_script.seed_themes()
    seed_script.seed_themes()

    with test_session_factory() as db:
        theme_count = db.scalar(select(func.count()).select_from(Theme))
        unique_key_count = db.scalar(select(func.count(func.distinct(Theme.key))))
        assert theme_count == 10
        assert unique_key_count == 10

    seed_script.seed_characters()
    seed_script.seed_characters()

    with test_session_factory() as db:
        character_count = db.scalar(select(func.count()).select_from(Character))
        assert character_count == len(seed_script.DEMO_CHARACTERS)
