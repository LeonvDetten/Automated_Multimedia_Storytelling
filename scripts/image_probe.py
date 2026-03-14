from app.db.session import SessionLocal
from app.repositories.episode_repository import get_episode
from app.services.job_service import _payload_from_episode
from app.storygen.story_service import generate_story
from app.storygen.openai_client import OpenAIClient
from app.core.config import get_settings

settings = get_settings()
with SessionLocal() as db:
    ep = get_episode(db, 116)
    payload = _payload_from_episode(db, ep)
    model_name = ep.model or "gpt-4.1-mini"
    client = OpenAIClient(api_key=settings.openai_api_key, model=model_name, langfuse_public_key=settings.langfuse_public_key, langfuse_secret_key=settings.langfuse_secret_key, langfuse_host=settings.langfuse_host)
    result = generate_story(db, payload, client)
    prompts = result.get('image_prompts') or []
    print('image_prompts count:', len(prompts))
    if prompts:
        prompt = prompts[0]
        print('prompt len', len(prompt))
        res = client.generate_image(prompt, size='512x512')
        print('res type:', type(res))
        try:
            print('res keys:', list(res.keys()))
        except Exception:
            print('cannot list keys')
        print('res repr snippet:', str(res)[:500])
