# Automated Multimedia Storytelling

Phase 1 provides a clean and extensible foundation for your story pipeline:
- FastAPI backend with REST endpoints
- PostgreSQL persistence via SQLAlchemy + Alembic
- Server-rendered web UI using Jinja2 + HTMX
- Background job stub (queued -> running -> completed)

## 1) Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Update `.env` with your local PostgreSQL credentials if needed.

## 2) Database migration

```bash
alembic upgrade head
```

## 3) Seed initial data

```bash
python -m scripts.seed
```

This inserts:
- 10 fixed themes
- demo characters
- one default story series

## 4) Run the app

```bash
uvicorn app.main:app --reload
```

Open:
- UI: `http://127.0.0.1:8000/`
- API docs: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`

## 5) Phase 1 API endpoints

- `GET /api/v1/themes`
- `GET /api/v1/characters`
- `POST /api/v1/characters`
- `GET /api/v1/series`
- `POST /api/v1/episodes`
- `GET /api/v1/episodes/{episode_id}`
- `GET /api/v1/jobs/{job_id}`

## 6) Web flow (Phase 1)

- `GET /` shows the episode input form.
- `POST /web/episodes/create` stores episode + job.
- `GET /web/jobs/{job_id}/status` is polled by HTMX.
- `GET /web/episodes/{episode_id}` shows episode detail.

## 7) Architecture notes

### Project structure

- `app/main.py` - app bootstrap, router registration, static mount
- `app/core/config.py` - environment configuration
- `app/db/` - base model + session lifecycle
- `app/models/` - relational schema models
- `app/repositories/` - focused DB operations
- `app/services/` - episode/job orchestration logic
- `app/api/v1/` - JSON API routes
- `app/web/routes.py` - HTML routes and form flow
- `app/templates/` - Jinja templates
- `scripts/seed.py` - idempotent seed data
- `tests/` - phase 1 API/seed coverage

### Job stub behavior

Background task simulation intentionally keeps logic simple for Phase 1:
1. queued
2. running (several progress updates)
3. completed

This prepares the codebase for real async workers in Phase 2+.

## 8) Testing

Run tests with:

```bash
pytest -q
```

If `pytest` is missing, install dependencies first using `pip install -r requirements.txt`.
