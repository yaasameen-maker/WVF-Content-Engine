# WVF Content Engine - Backend

AI-powered marketing content generation API for Women's Venture Fund.

## Quick Start

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your ANTHROPIC_API_KEY
   ```

3. **Test the generation pipeline (no server needed)**
   ```bash
   python test_generation.py
   ```

4. **Run the API server**
   ```bash
   uvicorn app.main:app --reload
   ```
   API will be available at `http://localhost:8000`

## API Endpoints

- `GET /` - Health check
- `POST /api/generate` - Generate content for an event

**Example request:**
```json
{
  "title": "Credit Building Workshop",
  "date": "July 16, 2024 at 2:00 PM ET",
  "speaker": "WVF Team",
  "registration_link": "https://example.com/register",
  "audience": "NYC women entrepreneurs",
  "description": "Learn how to build business credit..."
}
```

**Response:** Returns `social_post`, `hashtags`, and `newsletter` content as structured JSON.

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── schemas/             # Pydantic models (EventInput, outputs)
│   ├── services/            # Business logic
│   │   ├── brand_voice.py   # WVF brand guidelines & examples
│   │   ├── prompts.py       # Prompt templates per content type
│   │   └── generation.py    # Claude API integration
│   ├── routers/             # API endpoints
│   │   └── generate.py      # /api/generate endpoint
│   └── models/              # (Coming next: SQLAlchemy models)
├── requirements.txt
├── test_generation.py       # Standalone test script
└── README.md
```

## Tech Stack

- **FastAPI** - Web framework
- **Anthropic Claude** - LLM for content generation (Sonnet 4)
- **Pydantic** - Schema validation & structured outputs
- **SQLAlchemy** - ORM (coming next for persistence)
- **Alembic** - Database migrations (coming next)

## Next Steps

- [ ] Add SQLAlchemy models (`events`, `content_items` tables)
- [ ] Wire up Postgres persistence (Railway)
- [ ] Add content approval workflow (draft → approved → published)
- [ ] Add pagination/filtering for historical content
- [ ] Deploy to Railway

## Development

The backend currently generates content on-demand and returns it directly (no DB persistence yet). Next iteration will save all generated content with status tracking for the review/approval workflow.
