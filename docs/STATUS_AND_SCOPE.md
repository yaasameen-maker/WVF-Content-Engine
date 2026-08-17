# WVF Content Engine — Status, Scope, Budget & Approvals

Consolidated reference: what changed recently, what's confirmed in/out of
scope with timelines, what budget items are still outstanding, and what
specifically needs Maria's approval before it can move forward.

Last written: August 13, 2026. This is a snapshot — cross-check against
`CLAUDE.md`, `docs/PROJECT_CONTEXT.md`, and `docs/CONTENT_SCOPE.md` for
anything that may have moved since. Today is 6 weeks from Demo Day
(September 23, 2026).

---

## 1. Recent changes (August 2–13, 2026)

Chronological, from git history — everything below is committed and
pushed to `main` unless noted.

| Date | Change |
|---|---|
| Aug 2 | Repo scaffold, Railway service config for backend/frontend |
| Aug 3 | `CLAUDE.md`/`docs/` added; structural variant support for social posts and newsletters; real brand hex values from a newsletter screenshot; KeyMaker model + all 10 real Key Makers seeded |
| Aug 4 | Alembic migrations run automatically before app start on Railway; 6 modular newsletter block generators added |
| Aug 10 | Keymakers recruitment campaign copy seeded as reference material; content calendar (month-grid + list view); per-platform (Instagram/LinkedIn/Facebook) social post templates grounded in real WVF post screenshots; frontend deployed to Vercel (`vercel.json` scoping); event form reorganized (platform/Keymakers selection collapsed the manual-entry form behind a button) |
| Aug 11 | Fixed CORS so the deployed Vercel frontend can actually reach the Railway backend (was silently blocked — "Failed to fetch"); enlarged platform icon buttons and fixed brand color rendering (Instagram gradient, LinkedIn contrast) |
| Aug 12 | Social post + hashtag generation now returns 3 options concurrently for staff to compare and pick, instead of one fixed result — new `POST /api/content/select-social-variant` endpoint persists the picked pair |
| Aug 13 | README rewritten (stale Week 1 sprint log removed, still-accurate API/testing reference kept); sprint plans now archived as dated files (`docs/sprint-plans/`) instead of one file overwritten weekly; Keymakers Copy now shows the real WVF recruitment message **instantly** on selection (no AI call) via a new `GET /api/keymakers-stages/{stage_key}` endpoint; added a dedicated "AI Copy" option separate from platform/Keymakers selection |

**Net effect on the UI:** the event-form page now has 5 selectable
options — Instagram, LinkedIn, Facebook (all three currently disabled
placeholders pending real sample posts), Keymakers Copy (real static
reference copy, instant), and AI Copy (the full generation flow: fill
event details → Generate Campaign → compare 3 social post/hashtag
options → review/edit newsletter, flyer, and calendar).

---

## 2. Features confirmed IN scope — status and timeline

Per the confirmed priority order in `docs/PROJECT_CONTEXT.md`.

| # | Feature | Status | Notes |
|---|---|---|---|
| 1 | Newsletter / eblast / flyer generator | **Built** | Modular blocks (feature article, events list, grant/flyer, tips/CTA, member spotlight, boilerplate) have backend schemas + generators + endpoints; **not yet wired into the frontend** as its own flow — currently only the single-block legacy newsletter shape is exposed in the UI |
| 2 | Social post generation | **Built** | 3-option compare-and-pick flow live as of Aug 12; tone variants (Standard/Listicle/Quote-style) working; per-platform variants exist in the backend but have no static-template frontend surface yet (see §3) |
| 3 | Content calendar | **Built** | Month-grid + list view, reads real generated content by date |
| 4 | Hashtag generation | **Built** | Generated alongside social posts, 3 options per generation, same pick flow |
| 5 | Image prompts | **Built** | Text-only DALL-E-style prompt bundled into each social post output — no separate content type, no image files generated |

**Still open before full build-out:**
- Newsletter-blocks frontend UI (generate/review individual blocks) — the single largest built-but-unexposed gap right now
- "Full newsletter vs. individual blocks" generation model — open question, needs Nancy/Felix's answer (see §6)
- "Key Makers" definition reconciliation (Nancy's 10 real testimonial clients vs. Felix's 4 GHL personas) — blocks confidently tagging audience fields (see §6)

---

## 3. Features confirmed OUT of scope — what, why, and reopening cost

Per `CLAUDE.md`'s Out of Scope list and two prior scope-decision
conversations (Aug 8 manual-click publish decision; Aug 12 scheduler
question).

| Feature | Why it's out | If it gets reopened |
|---|---|---|
| Direct/automatic social publishing | Explicitly ruled out per program scope | Requires Meta App Review (see §4) — 6–8 weeks, longer than remains before Demo Day if not already started |
| Automatic post **scheduling** (fire-and-forget, no human click) | Needs a background job queue (RQ/Celery/similar) — explicitly excluded from this project's architecture given WVF's actual volume (3 posts/week, 2–4 newsletters/month) | Real new infrastructure, ~2–3 weeks build, plus it still needs the same Meta App Review as manual publish — doesn't remove that dependency, adds a second one on top of it |
| Custom graphics / video generation | Explicitly out of scope; confirmed again in the Nancy/Felix planning call | Not ruled out permanently — Nancy's own words: "remains out of scope for now but not ruled out" |
| Campaign performance analytics | Explicitly out of scope | No cost estimate produced — not currently being considered |
| Comment/DM management | Explicitly out of scope | No cost estimate produced — not currently being considered |
| Auth/user system (real login, roles) | Schema has `users.role`; no login flow built | Needed before multiple staff can safely use the tool with distinct permissions — not currently scheduled |

**Confirmed IN scope, not yet built** (distinct from "out of scope" —
this is groundwork already agreed to, just not started):
- Manual-click publish/send (human clicks "Post" every time; accounts
  connect via OAuth) — confirmed Aug 8. Gated entirely on Meta App
  Review timing (§4) and ESP selection (§5).
- Internal calendar scheduling (staff pick a future date for an approved
  draft; a human still posts it manually on the day) — proposed Aug 8,
  reaffirmed as the realistic option Aug 12, **not yet built or
  confirmed by WVF**. ~1 day of work once confirmed; no new
  infrastructure, reuses the existing calendar page.

---

## 4. Meta App Review — process and timeline

Sourced from Meta's own developer documentation (via Phyllo and Zernio's
Instagram Graph API guides, checked August 9, 2026). This is the longest
external lead-time item against Demo Day.

**Today (Aug 13) → Demo Day (Sept 23): 6 weeks. Meta's own stated review
window: 6–8 weeks.** If review takes the full 8 weeks, approval lands
*after* Demo Day. Even the fast end (6 weeks) leaves no buffer. **As of
this writing, submission has not yet been started.**

Required steps, in order:

1. **Convert Instagram to a Professional account** (Business or Creator,
   linked to a Facebook Page) — blocking; the publish API doesn't work
   on a personal account at all. Same-day.
2. **Create the Meta developer app** under WVF's business account (not a
   personal account — ownership needs to sit with WVF for the handoff
   after Demo Day).
3. **Complete business verification** — registered business
   documentation; can run in parallel with step 4.
4. **Build the publish endpoint, working end-to-end** — Meta's review
   requires a screencast of the actual permission
   (`instagram_content_publish`) working, so the code has to function
   *before* submission.
5. **Submit for App Review with the screencast** — this is the moment
   the 6–8 week clock actually starts.

**Bottom line:** this needs to start immediately regardless of what else
is in flight. It doesn't block other build work and isn't blocked by it —
but it is the single most time-sensitive open item on this entire list.

---

## 5. Email ramp-up — ESP options, cost, and timeline

Sourced from live vendor pricing pages (SendGrid/Mailgun/Postmark,
checked August 9, 2026 — confirm exact figures directly with each vendor
before committing, pricing pages change).

### Cost at WVF's target volume

| ESP | 10,000/mo | **50,000/mo (WVF's target)** | 100,000/mo |
|---|---|---|---|
| **SendGrid** | $19.95 | **$19.95** — cheapest at target volume | $89.95 |
| Mailgun | $15 | $35 | $90 |
| Postmark | $15–18 | ~$85–87 (estimated) | ~$150+ (estimated) |

SendGrid is roughly half of Mailgun's cost and a fraction of Postmark's
at WVF's actual target volume of 50–60k/month.

### DNS authentication

3 DNS records minimum (SPF, DKIM, DMARC) — set once, cost is $0 (just
records through WVF's existing domain registrar), does not scale with
volume. Recommendation: a dedicated sending subdomain (e.g.
`send.womensventurefund.org`) rather than the root domain, so a
bounce/complaint spike during warm-up never touches the main site or
admin email.

### The warm-up ramp — the real constraint

**A new sending domain cannot jump straight to 50–60k emails/month.**
Sending reputation has to be built gradually — typically **4–6 weeks**
from a cold domain to full target volume, regardless of which ESP is
picked. This ramp cannot be rushed or bought around.

**4–6 weeks of ramp-up against 6 weeks remaining to Demo Day means full
volume (50–60k/month) is very unlikely to be reached by Sept 23** if ESP
selection hasn't already happened. This was flagged to Felix previously
and remains unresolved as of this writing (see §6).

What **is** realistic by Demo Day: ESP selected, DNS authentication
live, and a manual-click "Send" button working — demoed at low volume (a
few hundred recipients), which doesn't require the full ramp to be
complete. Sending at the real 50–60k target is not realistic by Sept 23
under any ESP choice, purely due to the physics of the warm-up period,
not engineering effort.

---

## 6. What needs Maria's approval

Distinct, specific items — not a general "sign off on everything" ask.

| Item | What's being asked | Blocks |
|---|---|---|
| **`ANTHROPIC_API_KEY` budget sign-off** | Approve the ~$5–41/month total cost (hosting + Claude API — see table below) so the key can be added to Railway | **All live generation on the deployed site.** Everything is built and tested locally with a personal key; the hosted app cannot generate content until this is approved. This is the single most consequential open item — has been pending for over a week. |
| **Keymakers recruitment copy** | Approve the 4-message recruitment drip (initial + day 4/9/15 follow-ups) currently seeded as *reference* material in the codebase | Sending the actual campaign. Source `.docx` files are explicitly marked "still needs approval from Maria" — this is not send-ready output without her sign-off. |
| **ESP selection** (with Felix) | Confirm SendGrid (or an alternative) as the email service provider | Starting the DNS setup and warm-up ramp — every week without a decision here is a week lost from the 4–6 week ramp against a 6-week runway. |
| **Meta App Review submission** | Awareness/approval to begin — WVF's Instagram needs to convert to a Professional account and go through business verification, both of which touch WVF's real account | Manual-click social publish. This needs to start now regardless of other approvals given the 6–8 week window. |

### Verified budget (for reference, matches the ANTHROPIC_API_KEY ask above)

| Item | Monthly | 6-Week / 1.5-Month | Driver |
|---|---|---|---|
| Claude API (Sonnet 5) | $0.20 – $1 | $0.30 – $1.50 | Regeneration/edit volume, not raw content count |
| Hosting (frontend + backend) | $5 – $40 | $7.50 – $60 | Tier choice (dev/staging vs. commercial production) |
| **Total** | **$5 – $41** | **$8 – $61** | — |

AI usage itself is not the real cost driver — under $1/month even at the
high end. Hosting tier is what actually moves the total.

### Budgets not yet produced — need to be scoped

These are real, upcoming costs with no formal estimate delivered to
Maria yet, beyond the ESP pricing table in §5:

- **Email sending cost at scale** — the SendGrid/Mailgun/Postmark table
  above covers the ESP subscription itself, but does not yet include a
  combined "total cost of the email feature" figure (ESP + any
  additional deliverability tooling, if needed) — worth producing before
  the ESP conversation with Maria, not after.
- **Meta App Review — any associated cost.** Business verification and
  the developer app itself are free; flagging this as unconfirmed rather
  than assuming $0, since it hasn't been explicitly checked against
  Meta's current requirements.
- **Manual-click publish feature — ongoing hosting delta**, if the
  publish endpoint requires anything beyond current hosting (unlikely
  given it's still human-triggered, not a background service, but not
  yet explicitly confirmed as $0 marginal cost).

---

## Sources

- `CLAUDE.md`, `docs/PROJECT_CONTEXT.md`, `docs/CONTENT_SCOPE.md` — this
  repository
- Git commit history, `main` branch, Aug 2–13, 2026
- ESP pricing: SendGrid, Mailgun, Postmark pricing pages, checked Aug 9,
  2026
- Meta timeline: Phyllo's Instagram API integration guide, Zernio's
  Instagram Graph API overview, checked Aug 9, 2026
- Scope decisions: internal notes from the Aug 8 manual-click publish
  discussion and the Aug 12 scheduling scope discussion
