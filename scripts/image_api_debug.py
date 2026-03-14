from app.db.session import SessionLocal
from app.repositories.episode_repository import get_episode
from app.storygen.story_context import build_story_context
from app.storygen.prompt_builder import build_image_prompts
from app.storygen.openai_client import OpenAIClient
from app.core.config import get_settings

EPISODE_ID = 116

settings = get_settings()
print('OPENAI API KEY configured:', bool(settings.openai_api_key))

with SessionLocal() as db:
    ep = get_episode(db, EPISODE_ID)
    if not ep:
        print('episode not found')
        raise SystemExit(1)
    # Build a minimal payload for context
    from app.schemas.episode import EpisodeCreate
    payload = EpisodeCreate(
        user_prompt=ep.user_prompt,
        theme_id=ep.theme_id,
        series_id=ep.series_id,
        continuation_from_episode_id=ep.continuation_from_episode_id,
        character_ids=[link.character_id for link in ep.characters],
        target_duration_sec=ep.target_duration_sec,
        title=ep.title,
        is_standalone=ep.series_id is None,
        temperature=ep.temperature,
        max_output_tokens=ep.max_output_tokens,
    )
    context = build_story_context(db, payload)

    # Prefer to use existing script_text to build prompts
    story_text = ep.script_text or ''
    prompts = build_image_prompts(context, story_text, parts=4)
    print('built prompts:', len(prompts))
    for i, p in enumerate(prompts):
        print('\n--- PROMPT', i+1, 'len', len(p))

    client = OpenAIClient(
        api_key=settings.openai_api_key or '',
        model='gpt-image-1-mini',
        langfuse_public_key=settings.langfuse_public_key,
        langfuse_secret_key=settings.langfuse_secret_key,
        langfuse_host=settings.langfuse_host,
    )

    for i, p in enumerate(prompts):
        print(f'\nCalling image API for prompt {i+1}...')
        try:
            res = client.generate_image(p, size='1024x1024')
            print('type(res)=', type(res))
            try:
                # try as dict
                for k, v in (res.items() if hasattr(res, 'items') else []):
                    print('  key:', k, '->', type(v))
            except Exception:
                pass
            print('repr(res)[:800]=\n', repr(res)[:800])
        except Exception as e:
            print('Exception from generate_image():', e)
