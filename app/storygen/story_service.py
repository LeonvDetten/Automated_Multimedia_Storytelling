from typing import Any

from sqlalchemy.orm import Session

from app.schemas.episode import EpisodeCreate
from app.storygen.openai_client import OpenAIClient
from app.storygen.prompt_builder import build_prompt, build_image_prompts
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

    # Build image-generation prompts (4 parts) based on the generated story (if any)
    text = response.get("text", "")
    image_prompts = build_image_prompts(context, text, parts=4) if text else []

    response["image_prompts"] = image_prompts
    return response
