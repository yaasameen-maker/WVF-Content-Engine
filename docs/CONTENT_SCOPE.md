# WVF Content Engine — Generated Content Scope

What the engine actually generates today, as implemented in
`backend/app/services/prompts.py` and `backend/app/schemas/content.py`.
This is a snapshot of current code, not a spec — cross-check against those
files before relying on it, since structure is intentionally flexible (see
Content Structure Guide in @docs/PROJECT_CONTEXT.md).

Last written: August 5, 2026.

---

## Top-level content types

Generated together via `POST /api/generate`, driven by the event form
(`EventInput`: title, date, speaker, registration link, audience,
description).

| Content type | Output schema | Structural variants | What it produces |
|---|---|---|---|
| Social post | `SocialPostOutput` | 3 — Standard, Listicle, Quote-style | Caption (<150 words), 5–7 hashtags, image prompt, CTA |
| Hashtags | `HashtagsOutput` | 1 (none yet) | 3–5 primary brand tags + 5–7 topic-specific tags, with rationale |
| Newsletter (single-block legacy shape) | `NewsletterOutput` | 3 — Standard, Story-led, FAQ-style | Subject line, preview text, HTML body + plain-text body, CTA text/link |
| Flyer | `FlyerOutput` | 1 (none yet) | Headline, subheadline, body, CTA, footer details — text only, no graphic |
| Content calendar | `ContentCalendarOutput` | 1 (none yet) | Multi-week entries, platform-rotated (IG/LinkedIn/FB), angle-varied per post |

Variant selection is handled by `resolve_variant()`: a caller can request
`generate_new` (random), `avoid_recent` (random, excluding recently-used
variants), or an explicit variant key. Only social post and newsletter have
more than one variant registered today (`VARIANT_REGISTRY`).

## Newsletter modular blocks

Generated independently via the `newsletter_blocks` router — the 6-section
structure from the Content Structure Guide in PROJECT_CONTEXT.md. Each
block can be regenerated, swapped, or dropped per issue without touching
the others.

| Block | Schema | Notes |
|---|---|---|
| Feature article | `FeatureArticleBlock` | Long-form, educational — teaches something related to the event topic, not just a promo |
| Events list | `EventsListBlock` | One entry per generation call today; schema supports holding multiple |
| Grant / flyer | `GrantFlyerBlock` | Generates a *plausible* draft entry — prompt explicitly tells staff to replace with real, verified grant details before publishing |
| Tips / CTA | `TipsCtaBlock` | Short, reusable promotional block; loosely ties to event theme |
| Member / Key Maker spotlight | `MemberSpotlightBlock` | Accepts a real Key Maker's business name/owner/type (from the `key_makers` table) but deliberately avoids inventing quotes or personal details — placeholder story language until Nancy supplies real testimonials |
| Boilerplate | `BoilerplateBlock` | "About WVF" blurb + contact footer; phone/email/website are placeholders pending confirmed real values |

---

## Explicitly not generated

- **Image files** — every image reference in this system is a text
  description (`suggested_image_prompt`, `image_prompt`). No image
  generation or storage, per Out of Scope in PROJECT_CONTEXT.md.
- **Verified grant/funding data** — the grant/flyer block drafts a
  realistic-sounding entry; it is not sourced from any real grants
  database and is labeled as such in its own prompt.
- **Real Key Maker testimonial quotes** — even when a real Key Maker's
  identity is passed in, the prompt withholds inventing specific quotes,
  dollar figures, or personal details attributed to them.
- **Persona/audience-specific content filtering** — `event.audience` is
  free text and the only lever available; there is no dedicated logic
  distinguishing Nancy's 10 Key Makers from Felix's 4 GHL personas, or any
  other audience-based content branching. The "filtering" between
  formats (social vs. email vs. flyer) IS real, but it's architectural —
  each format has its own prompt function — not a client-facing toggle.
  See the interaction diagram linked below.
- **True image generation** — still out of scope; see "Reconsidering
  image generation" below for the cost/scope breakdown if this changes.

---

## Reconsidering image generation

Raised August 5–6, 2026 in follow-up to Felix's Keymakers email. Anthropic/
Claude has no image-generation API — Claude's only possible role stays
writing the *text* prompt, exactly as it does today via
`suggested_image_prompt` / `image_prompt`. Generating actual image files
would require a separate provider (OpenAI `gpt-image-1`, or a
Stability/SDXL-based provider).

**Cost, if added** (~40–75 images/month at WVF's cadence): roughly
**$2–9/month** for the image-gen API itself — negligible next to hosting,
consistent with the existing Claude API cost story in
PROJECT_CONTEXT.md's Cost & Budget section.

**Scope, if added** — the real cost, not the API bill:
1. New provider API key + integration (same budget-sign-off blocker as
   `ANTHROPIC_API_KEY` today).
2. New storage infra — none exists; PROJECT_CONTEXT.md's storage estimate
   is explicitly text-only, and this is exactly the trigger it names for
   revisiting that estimate. Needs an object store, a `content_items`
   schema migration (URL/blob reference, not just a text prompt field),
   and upload plumbing.
3. Brand-consistent output — reliably reproducing the navy/sky-blue
   block + leaf watermark + bold headline pattern needs either template
   compositing (generate/select a background, overlay text+logo
   programmatically) or heavy reference-image prompting. Meaningfully
   more engineering than the API call itself.
4. New review UI — current review flow is text-only editable fields;
   images need an approve/regenerate surface.
5. Still blocked on real logo files being in-repo (see Status in
   CLAUDE.md and the Brand Assets section of PROJECT_CONTEXT.md) — any
   compositing approach needs those first, in both SVG and transparent
   PNG (≥1000px), for both the standard and inverted logo marks.

**Cheaper alternative: premade template rotation.** Skip generation
entirely — WVF designs a small fixed library of on-brand template images
once (Canva), and the app *selects* one per generation (same
`generate_new` / `avoid_recent` / explicit-pick pattern already built for
structure variants in `prompts.py`) rather than creating new pixels.
Zero new provider, zero per-request cost, zero storage growth, brand
consistency guaranteed by construction. Still needs the real logo files
first, and a `template_image_url`-style field added to the response
shape. This is the recommended path if WVF wants "images" without taking
on the generation scope above.

---

## Known gaps relative to current external asks

(See Felix's August 5, 2026 email re: Keymakers campaign requirements,
and the August 6, 2026 follow-up covering email volume scaling and the
3-step interaction diagram.)

- **Resolved (August 6, 2026):** plain-text newsletter export —
  `NewsletterOutput.body_plain_text` now generated alongside the HTML
  body, with a copy-to-clipboard control on the review page.
- **Resolved (August 6, 2026):** persisted, browsable content calendar —
  `frontend/app/calendar/page.tsx` reads `GET /api/events` (already
  persisting every generated content item) and groups social posts +
  newsletters by event date. Scoped to those two content types only for
  now; flyer/hashtag/calendar-preview items aren't surfaced there yet.
  `Event.date` is free text (not a real date column — see
  `docs/SCHEMA.sql`), so entries that don't parse list separately rather
  than being silently dropped.
- No dedicated "Keymakers-specific vs. generic client" content filter —
  only `event.audience` free text exists today. Documented visually in
  the 3-step interaction diagram sent to Felix (August 6, 2026).
- **Not this codebase's job:** actually sending 50–60k emails/month
  (domain/IP warming, ESP selection, DNS auth) is infrastructure outside
  the Content Engine — see the ESP recommendation + timeline sent to
  Felix (August 6, 2026). A 4–6 week warm-up ramp means full volume by
  Demo Day (Sept 23, 2026) is unlikely if ESP selection hasn't started.

---

## `DESIGN.md` / calendar dashboard mockup — status

A more elaborate calendar UI mockup (`DESIGN.md` + accompanying HTML,
"WVF Content Engine" as a full marketing-ops dashboard — Campaigns,
Reports, Analytics, AI Insights with strategy recommendations,
multi-author tracking) was shared August 6, 2026. Per direct instruction:
**treat as a future-expansion visual template, not a current build
spec.** The calendar page actually built this sprint
(`frontend/app/calendar/page.tsx`) intentionally does NOT follow that
mockup's visual system (Montserrat/Hanken Grotesk, dark sidebar shell,
Material Symbols) — it matches the app's existing Tailwind navy/sky-blue
conventions instead. Dashboard/Campaigns/Reports/Analytics/AI-Insights
are explicitly out of scope per CLAUDE.md (analytics is listed in Out of
Scope; the rest was never discussed) and are not addressed by anything
built this sprint.
