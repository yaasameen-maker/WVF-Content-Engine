# WVF Content Engine

AI-powered marketing/content assistant for Women's Venture Fund (WVF), built
under Pursuit's SMB Builder Program (Pursuit x Google x Hispanic Federation).
Staff enter event/campaign details and get a branded content package
(newsletter/eblast/flyer, social posts, hashtags, content calendar, image
prompts) ready for review and approval.

- **Sprint plans** (dated, one file per week, never overwritten): [docs/sprint-plans/](./docs/sprint-plans/)
- **Full project context** (scope, content structure guides, open
  questions, program requirements): [docs/PROJECT_CONTEXT.md](./docs/PROJECT_CONTEXT.md)
- **What's actually generated today vs. known gaps:** [docs/CONTENT_SCOPE.md](./docs/CONTENT_SCOPE.md)
- **Current build status and conventions:** [CLAUDE.md](./CLAUDE.md)
- **Database schema:** [docs/SCHEMA.sql](./docs/SCHEMA.sql)

## Tech stack

- Frontend: Next.js (TypeScript) — `frontend/`
- Backend: FastAPI (Python) — `backend/`
- Database: PostgreSQL via Railway
- LLM: Anthropic Claude API, structured JSON output via tool-use

## Running locally

```bash
# backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload

# frontend
cd frontend && npm install && npm run dev
```

Backend available at `http://localhost:8000` (interactive docs at `/docs`).
Frontend available at `http://localhost:3000`. See
[backend/README.md](./backend/README.md) for backend-specific setup detail.

## API endpoints

- `GET /` / `GET /health` — health checks, including live DB connectivity
- `POST /api/generate` — generate content for an event and persist it
  (newsletter/flyer/calendar saved immediately; social post + hashtags
  return 3 options each for staff to compare — see
  `POST /api/content/select-social-variant` below)
- `POST /api/content/select-social-variant` — persist the social
  post/hashtags option staff picked from a `/api/generate` response
- `GET /api/events` / `GET /api/events/{id}` — list/get events with their
  generated content items
- `GET /api/content/{id}` / `PATCH /api/content/{id}` — get/edit a single
  content item's `body` and/or `status`
- `POST /api/content/{id}/approve` — mark a content item as `approved`
- `GET /api/variants/{content_type}` / `GET /api/keymakers-stages` —
  list available structure variants / Keymakers campaign stages, for
  frontend dropdowns
- `GET /api/newsletter-blocks/types` / `POST /api/newsletter-blocks` —
  generate/persist individual modular newsletter blocks (feature article,
  events list, grant/flyer, tips/CTA, member spotlight, boilerplate);
  built but not yet wired into the frontend — see
  [docs/sprint-plans/](./docs/sprint-plans/)

## Testing

The backend has an E2E test suite (`backend/tests/`) that exercises every
API route against a real, isolated SQLite database — Anthropic calls are
mocked with a fixed fake response so tests run free, fast, and without a
real API key, while everything else (HTTP layer, DB writes/reads, response
schemas, 404s, validation errors) runs for real.

```bash
cd backend
pip install -r requirements.txt
pytest -v
```

This suite runs automatically via GitHub Actions
(`.github/workflows/backend-e2e.yml`) on every push to `main` and every
pull request that touches `backend/`. The workflow also runs
`alembic check` to catch model/migration drift, and boots the FastAPI app
to confirm every route resolves — so a renamed field or broken endpoint
contract fails CI before it reaches a PR.
