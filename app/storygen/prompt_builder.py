"""Prompt construction helpers for Phase 2 story generation."""

from app.storygen.story_context import StoryContext


def build_prompt(context: StoryContext) -> str:
    """Build a story prompt from a StoryContext.

    Replace the string template below with your final prompt design.
    """

    characters_block = "\n".join(
        f"- {character.name} ({character.speech_style}): {character.description}"
        for character in context.characters
    )

    continuation_block = ""
    if context.continuation:
        continuation_block = (
            "\nContinuation context:\n"
            f"- Previous title: {context.continuation.title}\n"
            f"- Previous summary: {context.continuation.summary}\n"
        )

    theme_block = ""
    if context.theme_label:
        theme_block = f"Theme: {context.theme_label}\nTheme insight: {context.theme_description}\n"

    series_block = ""
    if context.series_title:
        series_block = f"Series: {context.series_title} (Episode {context.episode_number})\n"

    prompt = (
        "You are a professional story writer for a fairy-tale style series.\n"
        "Write in English. Output only the story text (no headings, no bullet points, no meta commentary).\n"
        "Length: 600–900 words, unless the user prompt clearly requests shorter.\n"
        "Tone: vivid, cinematic, emotionally resonant, suitable for narration.\n"
        "Structure: strong opening hook, clear rising tension, satisfying resolution.\n"
        "Theme handling: weave the theme subtly through actions, symbols, and choices.\n"
        "Character usage: give each listed character at least one distinct line or moment reflecting their speech style.\n"
        "If no characters are provided, avoid introducing named characters; focus on the narrator's perspective.\n"
        "Continuation: if a previous episode is provided, maintain continuity and build on it.\n"
        "\n"
        "\n=== THEME ===\n"
        f"{theme_block or 'None'}\n"
        "\n=== SERIES ===\n"
        f"{series_block or 'Standalone'}\n"
        "\n=== CHARACTERS ===\n"
        f"{characters_block or '- None'}\n"
        f"{continuation_block}"
        "\n=== USER PROMPT ===\n"
        f"{context.user_prompt}\n"
        "\nBegin the story now.\n"
    )

    return prompt
