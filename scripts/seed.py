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
        "name": "Oskar",
        "speech_style": "Rhythmic, punchy, and electric",
        "description": "An energetic rapper who charges every moment with lyrical fire and unstoppable groove.",
        "traits_json": {"temperament": "vibrant", "role": "hype navigator"},
    },
    {
        "name": "Tim",
        "speech_style": "Quiet, reflective, and poetic",
        "description": "An introverted literature student who observes deeply, speaks softly, and drops profound insights like hidden bookmarks in old novels.",
        "traits_json": {"temperament": "thoughtful", "role": "silent analyst"},
    },
    {
        "name": "Marc",
        "speech_style": "Chaotic, playful, and oddly philosophical",
        "description": "A walking festival of bad ideas and brilliant accidents who solves problems with questionable logic, kitchen utensils, and unexpected wisdom.",
        "traits_json": {"temperament": "chaotic-good", "role": "unofficial wildcard"},
    },
]

LEGACY_CHARACTER_RENAMES = {
    "Üpsti Üüüng": "Oskar",
    "Zinkus Aktiv": "Tim",
    "Bongo McWobble": "Marc",
}


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
        # Keep existing demo rows in sync when seeded names change.
        for old_name, new_name in LEGACY_CHARACTER_RENAMES.items():
            if old_name not in existing_names or new_name in existing_names:
                continue
            legacy_character = db.scalar(select(Character).where(Character.name == old_name))
            if legacy_character is None:
                continue
            legacy_character.name = new_name
            existing_names.remove(old_name)
            existing_names.add(new_name)

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
