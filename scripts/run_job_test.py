from app.db.session import SessionLocal
from app.repositories.episode_repository import get_episode
from app.services.job_service import run_storygen_job

EPISODE_ID = 116

with SessionLocal() as db:
    ep = get_episode(db, EPISODE_ID)
    if not ep:
        print('episode not found')
        raise SystemExit(1)
    print('BEFORE: ep', ep.id, 'status', ep.status)
    print('  image_url=', ep.image_url)
    print('  image_urls=', repr(ep.image_urls))
    job = None
    for j in ep.jobs:
        job = j
        break
    if job:
        print('  job', job.id, 'status', job.status, 'step', job.step, 'progress', job.progress_pct, 'error', job.error_message)
    else:
        print('  no job attached')

if job:
    print('\nRunning run_storygen_job for job id', job.id)
    run_storygen_job(job.id)

with SessionLocal() as db:
    ep2 = get_episode(db, EPISODE_ID)
    print('\nAFTER: ep', ep2.id, 'status', ep2.status)
    print('  image_url=', ep2.image_url)
    print('  image_urls=', repr(ep2.image_urls))
    for j in ep2.jobs:
        print('  job', j.id, 'status', j.status, 'step', j.step, 'progress', j.progress_pct, 'error', j.error_message)
