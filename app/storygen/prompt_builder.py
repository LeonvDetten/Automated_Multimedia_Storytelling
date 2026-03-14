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


def _excerpt_for_slice(story_text: str, index: int, total: int) -> str:
    """Return a short excerpt for the slice index (0-based) of the story_text."""

    text = story_text.strip()
    if not text:
        return ""

    # Split by paragraphs to keep scene boundaries when possible
    paragraphs = [p for p in text.split('\n\n') if p.strip()]
    if len(paragraphs) >= total:
        # choose paragraph slice
        per = max(1, len(paragraphs) // total)
        start = index * per
        excerpt = " ".join(paragraphs[start : start + per])
    else:
        # fallback: split by character length
        approx_len = max(120, len(text) // total)
        start = index * approx_len
        excerpt = text[start : start + approx_len]

    excerpt = " ".join(excerpt.splitlines())
    return (excerpt[:600] + "...") if len(excerpt) > 600 else excerpt


def build_image_prompts(context: StoryContext, story_text: str, parts: int = 4) -> list[str]:
    """Build a list of image-generation prompts dividing the story into `parts`.

    Each prompt should describe a distinct moment (quarter) of the story while
    requesting consistent characters and a unified visual style so the images
    read as a coherent sequence.
    """

    characters = ", ".join(c.name for c in context.characters) if context.characters else ""
    theme = context.theme_label or ""

    prompts: list[str] = []
    for i in range(parts):
        excerpt = _excerpt_for_slice(story_text, i, parts)
        parts_desc = (
            "opening/setting" if i == 0 else "inciting moment" if i == 1 else "climax" if i == parts - 2 else "resolution"
        )

        prompt_parts = [
            "Illustration prompt:",
            f"This is image {i+1} of {parts} illustrating the {parts_desc} of the same short story.",
            f"Scene excerpt: {excerpt}",
        ]

        if characters:
            prompt_parts.append(
                f"Characters present: {characters}. Keep the same character appearances across all images (consistent clothing, colors, and distinguishing traits)."
            )
        if theme:
            prompt_parts.append(f"Theme: {theme}")

        prompt_parts.extend(
            [
                "Visual guidance: maintain a consistent art style, color palette and recurring motifs so viewers recognize the sequence.",
                "Style: detailed digital painting, cinematic lighting, emotionally expressive faces. No text overlays.",
                "Output: square or 4:3 composition, small resolution acceptable (e.g. 512x512).",
            ]
        )

        prompts.append("\n".join(part for part in prompt_parts if part))

    return prompts


def build_image_prompt(context: StoryContext, story_text: str) -> str:
    """Backward-compatible single prompt (returns the first quarter)."""

    prompts = build_image_prompts(context, story_text, parts=4)
    return prompts[0] if prompts else ""
