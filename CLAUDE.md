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
  migration.
- Manual-click publishing (a human clicks "Post") is in scope and built for
  X; Instagram/Facebook follow the same pattern once Meta App Review clears.
  Still out of scope: fire-and-forget scheduling infrastructure (background
  job queues), analytics, comment/DM management, video generation. Note the
  `POST /api/social/x/run-scheduled-posts` endpoint added in Sept 2026
  (called by a Railway Cron Job) goes beyond the original "no scheduling"
  decision — confirm with WVF that it's wanted before extending it.

## Status (see @docs/PROJECT_CONTEXT.md and @docs/STATUS_AND_SCOPE.md for details)

- ✅ Backend generation pipeline (social post, hashtags, newsletter, image
  prompts) — code complete, 3 options per social post/hashtag generation.
  `ANTHROPIC_API_KEY` must be WVF's own key (needs Maria's budget sign-off);
  see docs/HANDOFF.md §3
- ✅ Frontend event form, review UI, and content calendar (WVF-branded).
  Content persists in Postgres; the calendar reads it by date. Platform
  tiles (Instagram/LinkedIn/Facebook/X/TikTok) offer AI copy or fixed
  templates; Keymakers recruitment copy is static reference text
- ✅ Postgres on Railway, Alembic migrations run before app start; frontend
  on Vercel, backend on Railway
- ✅ Newsletter modular blocks — schemas, generators, and
  `newsletter_blocks` router built; **not yet exposed as its own frontend
  flow**
- ✅ Key Makers real data seeded (`key_makers` public, `key_makers_private`
  PII via gitignored seed script)
- ✅ Approver passcode auth (`approvers` router, `manage_approvers.py`,
  email reset flow). Not a full multi-user login system; `users.role`
  in SCHEMA.sql is still unbuilt
- ✅ Staff photo library + photo/text composer (Cloudflare R2 storage,
  Pexels stock photos) — added as a proposed scope extension
- ✅ X (Twitter) manual "Connect X" / "Post to X" via OAuth 2.0 + PKCE,
  encrypted token storage, and secret-protected scheduled-post endpoint
- ⬜ Instagram/Facebook publishing — OAuth connect scaffolded
  (`meta_client.py`); publishing needs Meta App Review, and the Meta
  developer app is not yet created under WVF's Meta Business account
- ⬜ Exact brand colors — logo is in `frontend/public/wvf-logo.svg`, but
  `frontend/tailwind.config.ts` navy/sky-blue hex values are still
  screenshot-estimated (need a design-tool color picker)
- ⬜ Full-newsletter-vs-individual-blocks generation model: **blocked on
  client decision**, see Open Questions in PROJECT_CONTEXT.md

## Ownership note

Per the Pursuit contractor agreement, Work Product ownership transferred to
WVF upon completion payment and Demo Day (Sept 23, 2026) — both conditions
are now satisfied, so this repo is cleared for handoff to WVF/Felix. See
docs/HANDOFF.md for the transfer checklist (accounts, credentials, access,
and documentation to hand over).
