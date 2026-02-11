from typing import Any

from sqlalchemy.orm import Session

from app.schemas.episode import EpisodeCreate
from app.storygen.openai_client import OpenAIClient
from app.storygen.prompt_builder import build_prompt
from app.storygen.story_context import build_story_context


def generate_story(db: Session, payload: EpisodeCreate, openai_client: OpenAIClient) -> dict[str, Any]:
    """Main entry point for story generation.

    Steps:
    1. Build StoryContext from payload and DB.
    2. Build prompt from StoryContext.
    3. Call OpenAI client with prompt.
    4. Extract and return generated story text.
    """

    context = build_story_context(db, payload)
    prompt = build_prompt(context)
    response = openai_client.generate_text(
        prompt,
        temperature=payload.temperature,
        max_output_tokens=payload.max_output_tokens,
    )

    return response
