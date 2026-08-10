# WVF Content Engine

AI-powered marketing/content assistant for Women's Venture Fund (WVF), built
under Pursuit's SMB Builder Program (Pursuit x Google x Hispanic Federation).
Staff enter event/campaign details and get a branded content package
(newsletter/eblast/flyer, social posts, hashtags, content calendar, image
prompts) ready for review and approval.

See @docs/PROJECT_CONTEXT.md for full project context: confirmed scope,
content structure guides, cost/storage estimates, open questions, and
program requirements. Read it before making scope or architecture decisions.

See @docs/SCHEMA.sql for the database schema (matches the project ERD).

## Tech stack

- Frontend: Next.js (TypeScript), `frontend/`
- Backend: FastAPI (Python), `backend/`
- Database: PostgreSQL via Railway (provisioned; see Status below)
- LLM: Anthropic Claude API (`claude-sonnet-5`), structured JSON output via
  tool-use, one schema per content type (see `backend/app/schemas/content.py`)
- No background job queue (RQ/Celery/Redis) — generation is synchronous
  request/response. See "Out of Scope" in docs/PROJECT_CONTEXT.md for why.

## Commands

```bash
# backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload

# frontend
cd frontend && npm install && npm run dev
```

## Conventions

- Each content type (social post, hashtag set, newsletter) has its own
  Pydantic schema and prompt function — never merge them into one freeform
  text generation call. Keep outputs structured and independently editable.
- Content **structure is a flexible baseline, not a locked format** — WVF
  explicitly wants variation across posts/issues to keep engaging shifting
  social algorithms. Prompts should support multiple structural variants per
  content type, not hardcode one shape.
- Brand voice reference lives in `backend/app/services/brand_voice.py`,
  built from WVF's real social/newsletter samples — treat as the source of
  truth for tone and evergreen hashtags until WVF provides a formal brand kit.
- `content_items.platform` stays nullable/unused for now — it exists so a
  future posting-automation or GHL-campaign pipeline doesn't require a schema
  migration. Do not build OAuth/posting integrations against it yet.
- Do not build: direct social publishing, post scheduling, analytics,
  comment/DM management, video generation, background job queues. All
  explicitly out of scope.

## Status (see @docs/PROJECT_CONTEXT.md for details)

- ✅ Backend generation pipeline (social post, hashtags, newsletter) — code
  complete; `ANTHROPIC_API_KEY` not yet set in any hosted environment
  (blocked on Maria's budget sign-off), so only testable locally with a
  personal/dev key
- ✅ Frontend event form + review UI (WVF-branded, no persistence yet —
  content lives in sessionStorage)
- ✅ ERD / schema designed (@docs/SCHEMA.sql)
- ✅ Postgres provisioned on Railway; `DATABASE_URL` wired to the backend
  service (private network reference to the Postgres service) and Alembic
  migrations run automatically before app start
- ✅ Newsletter modular blocks (feature article, events list, grant/flyer,
  tips/CTA, member spotlight, boilerplate) — schemas, generators, and
  `newsletter_blocks` router built; see structure guide in PROJECT_CONTEXT.md
- ✅ Key Makers real data seeded — `key_makers` (public fields) and
  `key_makers_private` (PII, gitignored seed script) tables built and
  populated with WVF's real 10 Key Makers
- ⬜ Auth/user system not built — `users.role` exists in schema, no login yet
- ⬜ Real WVF logo files not yet in the repo — `frontend/tailwind.config.ts`
  navy/sky-blue hex values are still approximations
- ⬜ Full-newsletter-vs-individual-blocks generation model: **blocked on
  client decision**, see Open Questions in PROJECT_CONTEXT.md

## Ownership note

Per the Pursuit contractor agreement, Work Product ownership transfers to
WVF only upon completion payment and formal handoff after Demo Day
(Sept 23, 2026). Do not treat this repo as WVF/Felix's to modify or embed
elsewhere before that point, even if asked.
