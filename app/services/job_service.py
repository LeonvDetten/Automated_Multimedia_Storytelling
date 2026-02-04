"""Background job simulation service for phase 1."""

import time

from app.db.session import SessionLocal
from app.repositories.job_repository import update_job_state


def run_job_stub(job_id: int) -> None:
    """Simulate asynchronous processing by updating a job through fixed steps."""

    steps = [
        ("running", 25, "validating input", 0.1),
        ("running", 60, "assembling context", 0.1),
        ("running", 90, "preparing output", 0.1),
        ("completed", 100, "completed", 0.0),
    ]

    for status, progress_pct, step, delay in steps:
        if delay:
            time.sleep(delay)
        with SessionLocal() as db:
            update_job_state(db, job_id, status=status, progress_pct=progress_pct, step=step)
