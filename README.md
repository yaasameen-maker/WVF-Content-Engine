# WVF Content Engine

AI-powered marketing content generation platform for Women's Venture Fund (WVF), built for the SMB July 2026 cohort.

## Mini PRD

**WVF AI-Powered Marketing & Content Assistant**
Nancy Soto-Askew · SMB (July 2026) Cohort · Submitted July 8, 2026

### Problem Statement

At WVF, Nancy and the leadership team struggle with consistent social media content creation and marketing because of limited staff, funding, and time, leading to lower awareness, fewer registrations for technical assistance and training, and reduced community engagement.

### Users and Needs

Primary users: Anamaris (marketing/communications), Jessie (newsletter/content), and WVF interns (social media/design).

- Need rapid content creation without starting from scratch
- Need consistent, branded messaging across all platforms
- Need increased efficiency by automating repetitive tasks

### Solution Idea

An AI-powered WVF Marketing & Content Assistant where staff enter basic event details (title, date, speaker, registration link, audience, and description) and receive a complete, WVF-branded marketing campaign ready for staff review and approval — including social posts, emails, newsletter content, flyer copy, hashtags, image prompts, and a content calendar.

### Value Proposition

**For WVF staff** who struggle with consistent content creation due to limited staff and time, **the AI Marketing Assistant** provides automated marketing materials — **unlike** the current manual process, which results in inconsistent outreach and lower program registrations.

### Requirements

- User can enter event details through a simple form
- User can generate branded social media posts for all platforms
- User can create emails, newsletter content, and flyer copy automatically
- User can review and edit all AI-generated content before publishing
- User can generate a multi-week content calendar with hashtags and CTAs

### Out of Scope

- User cannot publish directly to social media platforms
- User cannot generate custom graphics or videos
- User cannot schedule posts from the application
- User cannot analyze campaign performance or analytics
- User cannot manage comments or direct messages

### Success Metrics (from original submission)

- Reduce content creation time by at least 75%
- Increase posting frequency to 3–5 posts per week
- Increase registrations for TA, workshops, and webinars
- Improve awareness and engagement across all platforms
- Allow staff more time for direct entrepreneur support

## Style Kit

### Branding Reference (confirmed from the logo/site)

- **Navy blue** — primary (nav bar, "Women's" wordmark, headline text)
- **Sky/steel blue** — secondary (leaf icon, "Venture Fund" wordmark, the "For Entrepreneurs/For Supporters" band)
- **White** — background/contrast
- **Concentric circle texture pattern** — subtle recurring background motif behind the logo and hero section
- **Leaf/sprout icon** — three-leaf plant growing upward, positioned to the right of the wordmark
- **Typography** — bold, blocky sans-serif for headlines ("WOMEN IN BUSINESS"), clean sans-serif for body/nav

| Color | Hex (approx.) | Usage |
| --- | --- | --- |
| Navy | `#1B2A5E` | "Women's" text, nav bar, headline text |
| Sky Blue | `#6FA8DC` | Leaf icon, "Venture Fund" text |
| White | `#FFFFFF` | Background/contrast |

These are close visual approximations — grab exact hex values with a color picker from the site/logo for pixel-perfect matching on a real mockup.

### Naming Lock-In

**WVF Content Engine** — the project name going forward, used consistently in scope docs, PRD updates, and anything client-facing.

## Tech Stack

### Backend
- **FastAPI** - Python web framework
- **Claude Sonnet 4** - LLM for content generation (via Anthropic API)
- **PostgreSQL** - Primary database (Railway)
- **SQLAlchemy** - ORM
- **Alembic** - Database migrations
- **Pydantic** - Schema validation & structured outputs

### Frontend
- **Next.js 14** - React framework (App Router)
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Vercel** - Deployment

## Project Structure

```
WVF-Content-Engine/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── database.py          # DB config & session management
│   │   ├── models/               # SQLAlchemy models
│   │   │   └── content.py       # Event & ContentItem models
│   │   ├── schemas/              # Pydantic schemas
│   │   │   └── content.py       # EventInput, all content outputs
│   │   ├── services/             # Business logic
│   │   │   ├── brand_voice.py   # WVF brand guidelines & style kit
│   │   │   ├── prompts.py       # Prompt templates (all 5 content types)
│   │   │   └── generation.py    # Claude API integration
│   │   └── routers/              # API endpoints
│   │       ├── generate.py      # /api/generate endpoint
│   │       └── content.py       # Events/content CRUD endpoints
│   ├── alembic/                  # Database migrations
│   ├── tests/                    # E2E pytest suite
│   ├── requirements.txt
│   ├── test_generation.py       # Standalone test script
│   └── pytest.ini
├── frontend/
│   ├── app/                       # Next.js app router
│   │   ├── page.tsx              # Event form (main page)
│   │   └── review/
│   │       └── page.tsx         # Content review page
│   ├── lib/
│   │   └── api.ts                # API client
│   ├── package.json
│   └── tailwind.config.ts
├── .github/workflows/
│   └── backend-e2e.yml           # CI: tests + migration drift check
└── README.md                     # This file
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL (or use Railway/Neon for cloud DB); SQLite is used automatically for local dev if `DATABASE_URL` is unset
- Anthropic API key

### Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add:
#   ANTHROPIC_API_KEY=your_key_here
#   DATABASE_URL=postgresql://user:pass@localhost:5432/wvf_content_engine
#   (omit DATABASE_URL to fall back to local sqlite:///./wvf_content_engine.db)

# Run database migrations
alembic upgrade head

# Test generation pipeline (no server needed)
python test_generation.py

# Start the API server
uvicorn app.main:app --reload
```

API available at `http://localhost:8000` (interactive docs at `/docs`)

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set up environment
cp .env.local.example .env.local
# Edit .env.local and set NEXT_PUBLIC_API_URL if the backend isn't on localhost:8000

# Start dev server
npm run dev
```

Frontend available at `http://localhost:3000`. The event form (`/`) posts to the backend and redirects to `/review`, where all five generated content types are shown in editable cards.

## Features (Current Build)

✅ **Content Generation** - Concurrent Claude API calls for all five content types (social post, hashtags, newsletter, flyer, calendar)  
✅ **Structured Outputs** - Uses Claude tool-use to force JSON matching Pydantic schemas  
✅ **Brand Voice** - Real WVF hashtags, tone, examples, and confirmed style-kit colors from IG/LinkedIn/FB/logo  
✅ **Database Models** - Events + ContentItems with status tracking (draft/approved/published)  
✅ **Alembic Migrations** - Version-controlled schema, applies cleanly to SQLite and Postgres  
✅ **Database Persistence** - `/api/generate` saves the event and all generated content as `draft`  
✅ **Content CRUD** - List/get events with content, get/update/approve individual content items  
✅ **Flyer Copy Generation** - Event flyer text (headline, subheadline, body, CTA, footer) matching WVF conventions  
✅ **Content Calendar** - Multi-week calendar with platform-varied entries, hashtags, and CTAs per post  
✅ **Event Form (Frontend)** - Next.js form matching the PRD's fixed input fields  
✅ **Review UI (Frontend)** - Editable cards for all five content types

## Features (Planned)

📋 **Content Approval Workflow (Frontend)** - Anamaris/Jessie review → approve → mark published, wired to the existing `/api/content/{id}/approve` endpoint  
📋 **Multi-Platform Support** - Instagram, LinkedIn, Facebook-specific post variations  
📋 **Image Prompt Generation (standalone)** - Currently embedded in the social post output (`suggested_image_prompt`); may split into its own content type later  
📋 **Auth & Access Control** - Role-based permissions (generator vs. approver)  
📋 **Railway + Vercel Deployment** - Production-ready hosting

## Testing

The backend has an E2E test suite (`backend/tests/`) that exercises every API route against a real, isolated SQLite database — Anthropic calls are mocked with a fixed fake response so tests run free, fast, and without a real API key, while everything else (HTTP layer, DB writes/reads, response schemas, 404s, validation errors) runs for real.

```bash
cd backend
pip install -r requirements.txt
pytest -v
```

This suite runs automatically via GitHub Actions (`.github/workflows/backend-e2e.yml`) on every push to `main` and every pull request that touches `backend/`. The workflow also runs `alembic check` to catch model/migration drift, and boots the FastAPI app to confirm every route resolves — so a renamed field or broken endpoint contract fails CI before it reaches a PR.

## API Endpoints

- `GET /` - Health check
- `GET /health` - Detailed health status, including live DB connectivity check
- `POST /api/generate` - Generate all content for an event and persist it (event + 5 content items, status=draft)
- `GET /api/events` - List all events with their generated content items, newest first
- `GET /api/events/{id}` - Get one event with all of its content items
- `GET /api/content/{id}` - Get a single content item
- `PATCH /api/content/{id}` - Update a content item's `body` and/or `status` (staff edits before approval)
- `POST /api/content/{id}/approve` - Mark a content item as `approved`

## Development Workflow

### This Week's Sprint (Mon–Sun, targeting Wed 4pm meeting + Week 1 close-out)

#### Day 1–2: Foundation & Environment ✅

**Repo scaffolding**
- Initialize monorepo: `backend/` (FastAPI/Python) + `frontend/` (Next.js/TS)
- `.gitignore`, `README.md`, basic folder structure
- Push initial commit, set up Railway project (backend + Postgres) and Vercel project (frontend) — even empty deploys now save time later

**Dev environment**
- Local `.env` files for both frontend/backend (Anthropic API key, DB connection string)
- Confirm Anthropic API access is working with a basic "hello world" call
- Postgres instance spun up on Railway, connection verified from FastAPI locally (SQLite used for local dev in the meantime)

#### Day 2–3: Data Model & Schema Design ✅

**Database schema (the "generation vs. state" split)**
- `events` table — title, date, speaker, registration_link, audience, description (matches PRD input form)
- `content_items` table — event_id (FK), content_type (social/newsletter/hashtag/etc.), platform (nullable, for future multi-platform), body (JSON), status (`draft`/`approved`/`published`), created_at, updated_at
- Gets the "don't rebuild later" architecture in place now, without building anything not yet needed

**Pydantic/JSON schemas per content type**
- Structured output schema for the top 3 priorities: social post, hashtags, newsletter content
- Each schema captures exactly what that format needs (social post = `caption`, `hashtags[]`, `suggested_image_prompt`; newsletter = `subject_line`, `body`, `cta`)

#### Day 3–4: Brand Voice Extraction ✅ (no Nancy input needed — pulled from samples)

- Compiled everything from the IG/LinkedIn/Facebook screenshots into `services/brand_voice.py`:
  - Full hashtag set observed: `#WomensVentureFund #WVFWomenEntrepreneurs #SmallBusinessSupport #WomenInBusiness #Entrepreneurship #NYCSmallBusiness #WVFCDFI #BusinessGrowth #LoanReady #CreditEducation #BusinessFunding #FinancialLiteracy #NYCBusiness`
  - Recurring content patterns: event promos (workshops, webinars), funding/grant announcements, inspirational quotes, partner co-branded posts
  - Tone: direct, benefit-forward, uses emojis sparingly (🚨, 📅, 🎯), CTA-driven ("Register Now", "Apply Today")
  - Color/template conventions: navy + white + sky blue, consistent header banner style
- This becomes the few-shot examples embedded directly in the prompt templates — usable regardless of what Nancy confirms Wednesday

#### Day 4–5: LLM Prompting Architecture ✅

- Core prompt structure for the top 3 priority content types (social post, hashtags, newsletter)
- Each prompt takes event details as structured input, includes the brand voice reference as few-shot context, and returns structured JSON matching the Pydantic schema
- `test_generation.py` — small test harness with a real sample WVF event ("Money & Credit" webinar) to manually review output quality

#### Day 5: Basic API Wiring ✅

- FastAPI endpoint that takes event input → calls Claude for each content type concurrently (`asyncio.gather`) → returns structured results
- No frontend UI needed yet this week — testing via `/docs`, curl, or Postman is enough to validate the generation pipeline works end-to-end

#### Day 6: Database Persistence & CI ✅

- `/api/generate` now persists the event + all 3 content items (status=`draft`) instead of just returning them
- Alembic migrations added and verified against the models (`alembic check`)
- CRUD endpoints: list/get events with content, get/update/approve individual content items
- E2E pytest suite + GitHub Actions workflow running on every push/PR (see [Testing](#testing))

#### Day 7: Remaining Content Types & Frontend Scaffold ✅

Picked up independently while waiting on Wednesday's answers — none of this depends on priority ranking, access/roles, or cost approval:

- Confirmed WVF's brand hex values (`#1B2A5E` navy, `#6FA8DC` sky blue, `#FFFFFF`) from the logo/site and locked them into `brand_voice.py` and the frontend Tailwind theme (see [Style Kit](#style-kit))
- Added the two remaining in-scope content types: flyer copy (`FlyerOutput`) and multi-week content calendar (`ContentCalendarOutput`) — same schema/prompt/service/router pattern as the original three, now generated concurrently as part of `/api/generate`
- Updated the E2E suite and fake fixture data for all 5 content types (13 tests, all green)
- Scaffolded the Next.js frontend: event form (`/`) matching the PRD's fixed fields, review page (`/review`) with editable cards for all 5 content types, Tailwind styled with the confirmed brand colors
- Locked in the project name **WVF Content Engine** for all client-facing docs going forward

#### Wednesday (mid-week, scheduled meeting)

- Bring working generation examples (even rough ones) to show Nancy — concrete output is more persuasive than describing plans
- Use the meeting to close the open questions (priority ranking, access/roles, ongoing cost approval) that unblock the rest of the build
- **This is also the Week 1 deadline moment** — leave with what's needed to finalize and send the revised PRD to Stef

#### End of Week (Week 1 close-out deliverable)

- Revised PRD updated with Wednesday's answers, signed off by Nancy, shared with Stef
- Repo pushed with working backend generation + persistence for all 5 content types
- Brand voice reference doc finalized as a living document for future prompt iteration
- Frontend event form + review UI built and working end-to-end against the local backend
- Remaining: wire the approval workflow's roles/permissions once Nancy confirms access, then deploy to Railway + Vercel (staging)

### Wednesday Meeting Agenda

- Demo working generation examples
- Close open questions:
  - Content priority ranking (social vs. newsletter vs. flyers)
  - Access/roles (who generates vs. who approves)
  - Ongoing cost approval for Claude API usage

## Contributing

This is a custom build for WVF. For questions or modifications, contact the development team.

## License

Proprietary - Women's Venture Fund

---

Built with ❤️ for WVF by the SMB July 2026 Cohort
