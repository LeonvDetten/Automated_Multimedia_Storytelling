# Automated Multimedia Storytelling

Phase 1 foundation for a story-to-video pipeline:
- FastAPI backend
- PostgreSQL persistence
- Server-rendered web UI with HTMX
- Background job stub for asynchronous flow

## Quick start

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy environment file:
   ```bash
   cp .env.example .env
   ```
4. Run the app:
   ```bash
   uvicorn app.main:app --reload
   ```

API docs are available at `http://127.0.0.1:8000/docs`.
