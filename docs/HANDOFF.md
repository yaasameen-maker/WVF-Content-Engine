# WVF Content Engine — Ownership Transfer Checklist

Both conditions in CLAUDE.md's ownership clause are now satisfied — Demo Day
(Sept 23, 2026) has passed and completion payment is confirmed — so this repo
is cleared for handoff to WVF. This document is the transfer checklist
CLAUDE.md's Ownership note points to; it did not exist before this pass and
is being created now, at the start of the actual handoff.

Primary WVF-side technical contact for this handoff: **Felix** (WVF's new
technical hire, separately building the Keymakers CRM/automation stack — see
PROJECT_CONTEXT.md's "Integration Notes"). Budget/account-creation approval
authority: **Maria** (WVF President).

Work through this top to bottom. Nothing here has been done yet — treat every
box as open until someone confirms it.

---

## 1. GitHub repo

- [ ] Transfer `WVF-Content-Engine` from the personal `yaasameen-maker`
      GitHub account/namespace to a WVF-controlled GitHub org or account
      (or add Felix/WVF as an owner, if a full transfer isn't possible
      immediately).
- [ ] Reconnect Vercel's and Railway's GitHub App integrations to the new
      repo location — a transfer alone does not migrate an existing
      deploy's git connection; each service needs to be re-pointed.
- [ ] Confirm `.github/workflows/backend-e2e.yml` (backend tests + Alembic
      drift check, runs on push/PR touching `backend/**`) still runs after
      the transfer. It uses no secrets, so nothing to reconfigure there.

## 2. Hosting accounts

- [ ] **Vercel** (frontend, `wvf-content-engine-two.vercel.app`) — verify
      who currently owns this Vercel account/team. Transfer the project to
      a WVF-owned Vercel team, or have WVF create one and redeploy from the
      (now WVF-owned) GitHub repo.
- [ ] **Railway** (backend + Postgres, `wvf-content-engine-production.up.railway.app`)
      — same ownership check and transfer/recreate decision as Vercel.
- [ ] **Resolve the duplicate frontend deploy config**: both
      `frontend/vercel.json` and `frontend/railway.json` exist. Per git
      history, the frontend was briefly scaffolded for Railway (Aug 2) then
      moved to Vercel (Aug 10) — `frontend/railway.json` is very likely
      orphaned. Check the Railway project dashboard for a live frontend
      service; if none exists, delete `frontend/railway.json` to avoid
      confusing a future maintainer about which platform is authoritative.
- [ ] Re-set every backend env var (see §4 below) on the new/transferred
      Railway project's Variables tab — these do not carry over
      automatically on a project transfer in all cases; verify after moving.
- [ ] Re-set `NEXT_PUBLIC_API_URL` on the new/transferred Vercel project if
      the backend's URL changes as part of this transfer.
- [ ] If a Railway Cron Job was configured for scheduled X auto-posting
      (calls `POST /api/social/x/run-scheduled-posts` with the
      `X-Scheduler-Secret` header), confirm it still exists and points at
      the correct backend URL after any transfer.

## 3. Third-party API keys / accounts — ownership decision needed for each

For each service below: either (a) transfer the existing account to WVF, or
(b) have WVF create its own account and swap the key. Do not leave any of
these under the contractor's personal ownership after handoff.

| Service | Used for | Status / action |
|---|---|---|
| **Anthropic (Claude API)** | All AI content generation | Currently a personal/dev key per CLAUDE.md — **never added to the hosted environment** in production use. WVF must generate its own Anthropic API key (after Maria's budget sign-off, ~$5–41/month) and set `ANTHROPIC_API_KEY` on Railway. Revoke/remove the contractor's key from any `.env` the contractor retains after handoff. |
| **Cloudflare R2** | Staff photo library + AI-generated image storage | Verify who owns the Cloudflare account behind `R2_ACCOUNT_ID`/`R2_ACCESS_KEY_ID`/`R2_SECRET_ACCESS_KEY`. If contractor-owned, WVF needs its own Cloudflare account + R2 bucket, with existing photos migrated (list via `GET /api/media/photos`, download each `public_url`, re-upload to the new bucket, update `photo_assets.object_key`/`public_url` rows). Also see the open follow-up in `object_storage.py`: connecting a real custom domain to the bucket instead of the free `.r2.dev` subdomain, which has unreliable CORS on real GET responses (worked around today via a backend proxy — see `GET /api/media/proxy/photos/{id}`). |
| **X (Twitter) Developer Portal** | OAuth app for manual "Connect X" / "Post to X" and scheduled auto-posting | Verify who owns the Developer Portal account that issued `X_CLIENT_ID`/`X_CLIENT_SECRET`. The **connected X account** is already correct (`@WomensVFund`, real WVF account) — it's the *app registration* itself that needs an ownership check. If contractor-owned, WVF should register its own X Developer Portal app (type must stay "Web App, Automated App or Bot", never "Native App" — that type can't issue a Client Secret), with **App permissions set to "Read and write and Direct message"** (this is the tier that actually grants `media.write`; the "Read and write" tier does not, despite the name — confirmed directly against X's API during this session). Reconnect X in the app afterward so the new token carries the right scopes. |
| **Meta Developer Portal** (Instagram + Facebook) | OAuth app for a future Instagram/Facebook publish integration — connecting works, publishing still needs Meta App Review | **Not yet created at all** as of the last status doc — this is a "create fresh," not "migrate," item. Must be created **under WVF's own Meta Business account**, not a personal one (this was already the documented requirement before handoff). Needs WVF's Instagram converted to a Professional account, linked to a WVF Facebook Page, plus Meta business verification, before App Review can even be submitted (6–8 week external review window). |
| **Pexels** | Free stock-photo search in the photo+text composer | Low-stakes, but reissue `PEXELS_API_KEY` under a WVF-owned Pexels account for continuity (a free key at pexels.com/api, no approval wait). |
| **Gmail / Microsoft 365 SMTP** | Sends the approver "forgot passcode" reset email only | Currently an interim/personal account per `email_sender.py`'s own docstring. WVF's real mail is Microsoft 365 at `wvf-ny.org` — replace `SMTP_USERNAME`/`SMTP_APP_PASSWORD` with a real WVF M365 mailbox + app password once a WVF M365 admin confirms SMTP AUTH is enabled for that mailbox. Note `SMTP_HOST`/`SMTP_PORT` need to change too (Microsoft 365 is `smtp.office365.com:587`, not Gmail's `smtp.gmail.com:465`) — these aren't in `.env.example` today, only documented in the module docstring; add them there as part of this change. |
| **Google AI Studio / Vertex AI** | Placeholder only — future image-generation phase, not built | Nothing to transfer; `IMAGE_GEN_API_KEY`/`IMAGE_GEN_MODEL` are unused today. |

## 4. Environment variables — full reference

Every var below needs to exist on the (new or transferred) Railway project
for the backend to run. Source of truth for descriptions:
`backend/.env.example` and the module docstrings noted.

**Required for the app to function at all:**
- `ANTHROPIC_API_KEY` — see §3
- `DATABASE_URL` — Railway sets this automatically for a Postgres service
  attached via private network reference; nothing to manually copy if the
  Postgres service itself is transferred/recreated correctly
- `ENVIRONMENT` — e.g. `production`
- `BACKEND_URL` — this backend's own public URL (must exactly match the
  X OAuth callback registered in the X Developer Portal)
- `FRONTEND_URL` — the Vercel frontend's public URL
- `TOKEN_ENCRYPTION_KEY` — Fernet key encrypting stored OAuth tokens
  (X/Instagram/Facebook) at rest. **Back this up somewhere outside Railway
  before any account transfer** — losing it orphans every already-connected
  social account with no recovery path other than reconnecting from scratch.
- `CORS_ALLOWED_ORIGINS` — comma-separated extra allowed frontend origins
  (the Vercel URL) beyond `localhost:3000`. **Not currently listed in
  `backend/.env.example`** — add it there; referenced only in
  `app/main.py`'s comments today.

**X integration:**
- `X_CLIENT_ID`, `X_CLIENT_SECRET` — see §3
- `SCHEDULER_SECRET` — shared secret protecting the scheduled auto-post
  endpoint; generate a fresh one if rotating credentials post-handoff
  (`python -c "import secrets; print(secrets.token_urlsafe(32))"`), and
  update the Railway Cron Job's `X-Scheduler-Secret` header to match

**Meta integration (once built):**
- `META_APP_ID`, `META_APP_SECRET` — see §3

**Email (passcode reset):**
- `SMTP_USERNAME`, `SMTP_APP_PASSWORD` — see §3
- `SMTP_HOST`, `SMTP_PORT` — optional overrides, not yet in
  `.env.example` (see §3); needed once the SMTP account moves to M365

**Object storage:**
- `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`,
  `R2_BUCKET_NAME`, `R2_PUBLIC_BASE_URL` — see §3

**Stock photos:**
- `PEXELS_API_KEY` — see §3

**Not yet used (future scope):**
- `IMAGE_GEN_API_KEY`, `IMAGE_GEN_MODEL` — placeholders only

**Frontend (`frontend/.env.local.example` / Vercel project settings):**
- `NEXT_PUBLIC_API_URL` — the only frontend env var; must point at the
  Railway backend's real URL

## 5. Credential rotation (recommended, not just "transfer as-is")

Since the contractor has held all of the above secrets locally, rotate the
sensitive ones during handoff rather than simply handing over the existing
values — this ensures the contractor's local `.env` copies stop being valid
access paths once handoff is complete:

- [ ] Rotate the Railway Postgres password (`DATABASE_URL`)
- [ ] Rotate `TOKEN_ENCRYPTION_KEY` — note this invalidates every currently
      stored OAuth token, so plan to reconnect X (and Instagram/Facebook,
      once built) immediately after rotating
- [ ] Rotate `SCHEDULER_SECRET` and update the Railway Cron Job to match
- [ ] Reissue `PEXELS_API_KEY`, `R2_ACCESS_KEY_ID`/`R2_SECRET_ACCESS_KEY`
      under WVF-owned accounts (covered in §3, listed again here as
      rotation items)
- [ ] Confirm the contractor's personal `ANTHROPIC_API_KEY` and SMTP
      credentials are removed from any local `.env` the contractor retains
      after this handoff — these should never be the ones running in
      production regardless

## 6. Documentation state

- `CLAUDE.md`, `docs/PROJECT_CONTEXT.md`, `docs/SCHEMA.sql` are the primary
  technical reference and are reasonably current as of this handoff, but
  **CLAUDE.md's own "Status" section has drifted** — e.g. it still says
  `ANTHROPIC_API_KEY` is unset in any hosted environment and that review-page
  content "lives in sessionStorage" with no persistence, both of which are
  now out of date (generation is live, content persists via Postgres/the
  calendar). Recommend a full doc-refresh pass separate from this checklist
  so WVF inherits accurate docs, not a stale snapshot.
- `docs/STATUS_AND_SCOPE.md` (last written Aug 17, 2026) is a point-in-time
  snapshot, not a living doc — treat it as historical context, not current
  status, once this handoff is further along.
- `docs/sprint-plans/` was removed as part of this handoff pass — dated
  weekly progress logs with no code references, superseded by this
  document and `STATUS_AND_SCOPE.md`.

## 7. Closing the loop

- [ ] Once every box above is checked, send a short written confirmation
      (email is fine) to WVF/Felix and Maria stating the handoff is
      complete, what was transferred, and the date — this closes out the
      Pursuit contractor agreement's ownership-transfer clause in writing,
      not just in practice.
- [ ] After that confirmation, the contractor should no longer retain
      working copies of any production secret listed in §4 beyond what's
      needed for a reasonable transition-support window, if one is agreed.
