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
        "You are a professional story writer for fairy-tales.\n"
        "Write in English. Output only the story text (no headings, no bullet points, no meta commentary).\n"
        f"Target length: about {context.target_words} words (do not exceed!!!).\n"
        "If you are near the limit, wrap up quickly and resolve the main conflict! No cliffhanger!\n"
        "Tone: vivid, cinematic, emotionally resonant, suitable for narration, concise.\n"
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


def build_image_prompt(context: StoryContext, story_text: str) -> str:
    """Build an image-generation prompt that matches the generated story.

    The prompt should be descriptive and focus on a single evocative scene
    from the story, include characters and theme when available, and suggest
    a vivid art style suitable for illustration.
    """

    # Choose a short scene description from the start of the story_text
    scene_excerpt = "".join(story_text.strip().splitlines()[:3])
    scene_excerpt = (scene_excerpt[:600] + "...") if len(scene_excerpt) > 600 else scene_excerpt

    characters = ", ".join(c.name for c in context.characters) if context.characters else ""
    theme = context.theme_label or ""

    prompt_parts = [
        "Illustration prompt:",
        "Create a single, high-quality, cinematic illustration that matches the following short story excerpt and theme.",
        f"Scene excerpt: {scene_excerpt}",
    ]

    if characters:
        prompt_parts.append(f"Characters present: {characters} (distinct visual traits, emotionally expressive)")
    if theme:
        prompt_parts.append(f"Theme: {theme}")

    prompt_parts.extend([
        "Focus on atmosphere, lighting, and emotion. Use a vivid, cinematic color palette.",
        "Style: detailed digital painting, cinematic lighting, shallow depth of field. No text overlays.",
        "Output: a single 1:1 or 4:3 scene suitable for a story thumbnail.",
    ])

    return "\n".join(part for part in prompt_parts if part)
