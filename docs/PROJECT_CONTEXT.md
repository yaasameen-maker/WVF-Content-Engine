# WVF Content Engine — Project Context

Full reference for scope, decisions, and open items. CLAUDE.md imports this
file — read it before making scope, priority, or architecture calls.

Last updated: August 3, 2026. Supersedes the original Mini PRD (July 8, 2026).

---

## Problem Statement

At WVF, Nancy and the leadership team struggle with consistent social media
content creation and marketing because of limited staff, funding, and time,
leading to lower awareness, fewer registrations for technical assistance and
training, and reduced community engagement.

The real bottleneck, confirmed in discovery: **drafting and deciding when
content is "good enough" to send** — not publishing mechanics. Hashtags have
historically been an afterthought (added post hoc, sometimes in comments)
rather than decided during drafting.

## Users & Access

- **Content creators:** Anamaris (marketing/comms), other marketing
  staff/interns — generate content
- **Approver:** Nancy — sole final sign-off before anything is sent/published
- No one else has publish authority. Build the review/approval flow around
  this single-approver model.

## Solution / Value Proposition

An AI-powered WVF Marketing & Content Assistant ("WVF Content Engine") where
staff enter event/campaign details and receive a complete, WVF-branded
content package ready for review and approval — covering social posts, a
modular newsletter/eblast/flyer, hashtags, image prompts, and a content
calendar.

---

## Confirmed Feature Priority

Reordered per Nancy's direct instruction (social post generation moved to
#2, hashtag generation moved to #4):

| Priority | Feature | Notes |
|---|---|---|
| 1 | Newsletter / eblast / flyer generator | One modular generator, not three separate features — see Content Structure Guide |
| 2 | Social post generation | 3x/week. Includes event AND general content (holidays, mentor recruitment) |
| 3 | Content calendar | ~6-week / 1.5-month horizon. Not a separate content type — assembled from generated items by date |
| 4 | Hashtag generation | Generated alongside social posts, not standalone. Wants real strategy, not ad-hoc suggestions |
| 5 | Image prompts | Text descriptions only — no image files generated or stored |

**The priority ORDER is confirmed. The content STRUCTURE below is intentionally
not locked — see Content Structure Guide.**

---

## Content Structure Guide

> **IMPORTANT:** These structures are a starting baseline, not a fixed spec.
> WVF wants to keep testing and varying format to work with (not get
> flagged/fatigued by) social algorithms. Locking into one repeated template
> works against that goal. The generator should support multiple structural
> variants per content type, not one hardcoded format. Treat every structure
> below as a default to follow, override, or remix — not a rule to enforce.

### Social Media Posts

Derived from a review of WVF's real Instagram/LinkedIn post history — a base
pattern, not the only allowed format.

| Element | Pattern observed | Generation rule |
|---|---|---|
| Headline | Short, bold, 3–6 words, title case or caps ("GRANT OPPORTUNITY," "FINANCIAL LITERACY FRIDAY") | Always generate a short headline separate from body text |
| Recurring series | "Financial Literacy Friday," "Grant Opportunity," "Top 3 [Topic]," quote posts, "Are You Ready?" seasonal | Let staff tag a post as part of an existing series to reuse its known format |
| Body copy | Benefit-forward, plain language, short paragraphs/bullets, ends with direct CTA | Keep under ~150 words; CTA required every time |
| Visual pattern | Navy/sky-blue block, bold white sans-serif headline, WVF leaf logo watermark, occasional real photo | Image prompts should describe this template style, not generic stock imagery |
| Hashtags | Historically inconsistent, ad hoc, sometimes in comments | Generate in-caption, not comment-appended; mix evergreen + event-specific |

### Newsletter / Eblast / Flyer

Derived from a real WVF newsletter sample (Canva-designed, distributed via
Vertical Response) — also a base template, not locked. **Not a single flat
email — a modular, multi-section publication.** Flyer-style content lives
inside this format as the Grant/Flyer block, not as a separate feature.

| Block | Contains | Notes |
|---|---|---|
| Feature article | Headline, body copy, "Read More" CTA | Long-form, educational tone |
| Upcoming events list | Bulleted: title, date, time, register link | Same source data as social posts |
| Grant / flyer block | Repeatable entries: name, amount, deadline, eligibility, link | This is where "flyer copy" actually lives |
| Tips / CTA block | Promotional headline + short pitch + image | Short, reusable across issues |
| Member / Key Maker spotlight | Client story headline, body, "Read More" link | Home for Key Makers testimonials — needs their identifying details |
| Boilerplate + footer | "About WVF" blurb, contact info, social icons | Static/reused, low generation priority |

WVF may want to swap, drop, or reorder blocks per issue rather than always
producing the same six sections.

**Open question:** full assembled newsletter generated per issue, or
individual blocks generated on demand and assembled manually in Canva? See
Open Questions below.

### Hashtags

Generated alongside social posts (not a standalone step): an evergreen set
plus event/topic-specific tags, replacing the prior ad hoc approach.

### Content Calendar

A ~6-week / 1.5-month forward view assembling scheduled social posts and
newsletter/eblast issues by date. Derived from existing generated content —
not a separately authored content type.

### Image Prompts

Text descriptions only, matching the visual pattern above. No image files
are generated or stored by this tool.

---

## Content Cadence

- Social: 3x/week — event content AND general content (holidays, mentor asks)
- Eblasts: 2–4x/month, tied to events — sometimes combining two events into
  one send to conserve Vertical Response's 10,000 credit/month limit
- Content calendar horizon: ~6 weeks / 1.5 months out — next month approved
  by the middle of the current month

---

## Brand Assets

- Real WVF logo files (leaf-on-white and inverted white-on-navy versions)
  **not yet in the repo** — still waiting on an actual exported PNG/SVG
  from the team (a Canva editor link doesn't count; need a real Share →
  Download export).
- Real newsletter/eblast sample screenshot reviewed — used to estimate
  `frontend/tailwind.config.ts` hex values (`navy: #4A7EBB`,
  `sky-blue: #87ACD1`) and `backend/app/services/brand_voice.py`'s
  VISUAL_STYLE. These are screenshot-estimated, not pixel-picked from a
  source file — replace with exact values once real brand files arrive.
- No formal brand kit exists — WVF's consistency is "through repetition,"
  not a documented style guide. `brand_voice.py` is effectively the first
  documented brand reference WVF has had.

---

## Cost & Budget — Verified

Recalculated using Anthropic's published Claude API pricing (not a rough
placeholder). Supersedes the $1–20/month and "Claude 3.5 Sonnet" figures
discussed verbally on the call — that model is prior-generation; current
tier is Claude Sonnet 5.

| Item | Monthly | 6-Week / 1.5-Month | Driver |
|---|---|---|---|
| Claude API (Sonnet 5) | $0.20 – $1 | $0.30 – $1.50 | Regeneration/edit volume, not raw content count |
| Hosting (frontend + backend) | $5 – $40 | $7.50 – $60 | Tier choice (dev/staging vs. commercial production) |
| **Total** | **$5 – $41** | **$8 – $61** | — |

AI usage is NOT the real cost driver — stays under $1/month even at the high
end. Hosting tier is what actually moves the total. Note: Anthropic's
standard rate ($3/$15 per MTok) takes effect September 1, 2026, replacing
the introductory rate ($2/$10) — falls inside the build window, doesn't
meaningfully change the total at this volume.

**Pending final sign-off from Maria (WVF President)** — until approved, the
Anthropic API key cannot be added to any hosting environment (Railway
included). Local/dev work that doesn't call `/api/generate` is unaffected;
see CLAUDE.md Status.

---

## Data Storage Estimate

All generated content is text (JSON), not media files.

| Content type | Est. size/item | Est. monthly volume |
|---|---|---|
| Social post (text + hashtags) | ~1–2 KB | ~13/month → ~15–25 KB/month |
| Newsletter/eblast (all blocks) | ~5–10 KB | ~2–4/month → ~10–40 KB/month |
| Hashtag sets | < 1 KB | Negligible — bundled with posts |
| Image prompts (text only) | < 1 KB | Negligible |
| Content calendar entries | < 1 KB each | Derived from above |

> **This is an ESTIMATE based on the current proposed structures — not
> final.** Structures are intentionally flexible and may expand as the build
> progresses (more structural variants, longer-form content, additional
> content types), so actual storage may increase. Still expected to stay
> well under free-tier database limits, but revisit this figure as the build
> evolves rather than treating it as fixed. Changes materially only if
> actual image files (not just prompts) get generated/stored in the future.

---

## Requirements

- User can enter event/campaign details through a simple form
- User can generate branded social media posts matching WVF's structure
- User can generate newsletter/eblast/flyer content as modular, reusable blocks
- User can review and edit all AI-generated content before publishing
- User can generate a multi-week content calendar with hashtags and CTAs

## Out of Scope

- Direct publishing to social media platforms
- Custom graphics or video generation
- Post scheduling automation
- Campaign performance analytics
- Comment/DM management
- Background job queue (RQ/Celery/Redis) — generation is synchronous
  request/response at WVF's volume (3 posts/week, 2–4 newsletters/month);
  revisit only if volume or async requirements change materially

## Success Metrics

- Reduce content creation time by at least 75%
- Increase posting frequency to 3–5 posts/week (confirmed achievable —
  matches Nancy's stated 3x/week target)
- Increase registrations for TA, workshops, and webinars
- Improve awareness/engagement across all platforms
- Allow staff more time for direct entrepreneur support

---

## Open Questions — Needs Client Confirmation

| Topic | What needs clarifying |
|---|---|
| Full newsletter vs. individual blocks | Complete assembled newsletter per issue, or individual blocks generated on demand for manual Canva assembly? |
| General content input | Non-event social posts (holidays, mentor recruitment) need a lighter input path than the event form — not yet designed |
| "Key Makers" definition | Nancy: 10 specific WVF clients with video testimonials. Felix/GHL doc: 4 broad audience personas (Microloan Applicants, Donors, Corporate Partners, Community Registrants). **These are different concepts** — confirm before tagging audience fields |
| Website embed | Felix asked about embedding this tool into the Key Makers website he's building. Technically feasible in concept; architecture (auth, domain, iframe vs. component) not scoped. Treat as future conversation, not committed spec — also gated by the ownership timeline (see below) |

---

## Integration Notes — Felix's Ecosystem (Keymakers CRM automation)

Felix (WVF's new technical hire) is separately building a CRM/automation
stack (Salesforce → GoHighLevel migration, entrepreneur intake form,
Givebutter integration, Slack ops pings) for the "Keymakers" membership
campaign. **These are NOT part of this project's scope.**

Real overlap points (informational, not action items unless noted):

- `events.audience` is free text — staff can already type any of the 4 GHL
  personas into it today for persona-tuned copy. No schema change needed.
- `brand_voice.py` can be handed to Felix's team so GHL email drips and this
  tool's output sound like the same organization.
- `content_items.platform` (nullable) leaves room for a future "approved
  newsletter → GHL campaign" pipeline, if formally scoped later. Not built.
- Felix's Slack notification layer (n8n/Zapier) is a plug-in point for a
  future "draft ready for review" alert from this tool, rather than building
  a separate Slack integration. Not built — scaffolding only, for handoff.

**Ownership clarification:** Felix's automation doc lists "Custom React UI
(Nancy's AI Assistant)" as one of his ecosystem's own tools, and separately
mis-describes it as OpenAI-powered. It is Anthropic Claude-based and is a
separately contracted Pursuit deliverable, not part of Felix's build. Per
the Pursuit contractor agreement, Work Product ownership transfers to WVF
only upon completion payment and formal handoff after Demo Day (Sept 23,
2026) — do not treat this repo as available for Felix's team to modify or
embed before that point.

---

## Program Requirements (Pursuit SMB Builder Program)

- Contract term: July 24 – September 23, 2026 (7 weeks: 6-week core build +
  demo prep week)
- Weekly client contact minimum, logged
- Weekly 1:1 with Stef (Pursuit mentor)
- Daily standup + weekly check-out in builder Slack channel
- Demo Day: September 23, 2026, at Google HQ — live demo required, co-present
  with Nancy
- Recurring client call: Wednesdays, 4:00 PM

## Action Items (rolling — update as resolved)

- [ ] Confirm full-newsletter-vs-individual-blocks generation model with Nancy/Felix
- [ ] Confirm "Key Makers" definition before tagging audience fields
- [ ] Request Key Makers identifying details (names, business names, photos,
      testimonial quotes/video links) — slots into the Member Spotlight block
- [x] Provision Postgres (Railway) — done; `DATABASE_URL` wiring to backend
      service in progress
- [ ] Apply `docs/SCHEMA.sql` via Alembic once `DATABASE_URL` is confirmed
- [ ] Build auth/user system (schema has `users.role`, no login yet)
- [ ] Await Maria's budget sign-off (expected Wednesday call) — blocks
      adding `ANTHROPIC_API_KEY` to any hosted environment
- [ ] Obtain real logo files in-repo (`frontend/public/` or similar) and
      extract accurate hex values
