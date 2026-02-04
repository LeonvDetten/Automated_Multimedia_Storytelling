"""Seed script for phase 1 reference data.

Run with:
    python -m scripts.seed
"""

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.character import Character
from app.models.story_series import StorySeries
from app.models.theme import Theme

THEMES = [
    ("envy", "Envy", "A story about jealousy, comparison, and desire."),
    ("betrayal", "Betrayal", "A story about trust being broken and its consequences."),
    ("love", "Love", "A story about connection, devotion, and emotional growth."),
    ("power", "Power", "A story about influence, responsibility, and control."),
    ("guilt", "Guilt", "A story about remorse and the search for redemption."),
    ("hope", "Hope", "A story about endurance and optimism against odds."),
    ("courage", "Courage", "A story about fear confronted by brave choices."),
    ("loss", "Loss", "A story about grief and adaptation."),
    ("revenge", "Revenge", "A story about retaliation and moral cost."),
    ("forgiveness", "Forgiveness", "A story about healing and letting go."),
]

DEMO_CHARACTERS = [
    {
        "name": "Elara Quinn",
        "speech_style": "Calm and reflective",
        "description": "A strategic navigator who speaks with precise analogies.",
        "traits_json": {"temperament": "measured", "role": "navigator"},
    },
    {
        "name": "Jax Mercer",
        "speech_style": "Bold and fast-paced",
        "description": "A risk-taker who turns tension into momentum.",
        "traits_json": {"temperament": "impulsive", "role": "scout"},
    },
    {
        "name": "Nora Vale",
        "speech_style": "Warm and empathetic",
        "description": "A mediator who reframes conflict and protects group trust.",
        "traits_json": {"temperament": "empathetic", "role": "mediator"},
    },
]


def seed_themes() -> None:
    """Insert fixed theme options if they are missing."""

    with SessionLocal() as db:
        existing_keys = set(db.scalars(select(Theme.key)).all())
        for key, label, description in THEMES:
            if key in existing_keys:
                continue
            db.add(Theme(key=key, label=label, description=description, active=True))
        db.commit()


def seed_characters() -> None:
    """Insert demo characters for first UI tests."""

    with SessionLocal() as db:
        existing_names = set(db.scalars(select(Character.name)).all())
        for payload in DEMO_CHARACTERS:
            if payload["name"] in existing_names:
                continue
            db.add(Character(**payload, active=True))
        db.commit()


def seed_default_series() -> None:
    """Create one initial story series used by episode creation."""

    with SessionLocal() as db:
        existing = db.scalar(select(StorySeries).where(StorySeries.title == "Default Series"))
        if existing:
            return
        db.add(StorySeries(title="Default Series", description="Initial series for phase 1", language="en"))
        db.commit()


def main() -> None:
    """Run all seed steps."""

    seed_themes()
    seed_characters()
    seed_default_series()
    print("Seed completed.")


if __name__ == "__main__":
    main()
