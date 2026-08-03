-- WVF Content Engine — Database Schema
-- Matches the project ERD (see docs/PROJECT_CONTEXT.md for the full design
-- rationale). Written for PostgreSQL. Not yet applied to a live database —
-- see CLAUDE.md Status section.

CREATE EXTENSION IF NOT EXISTS "pgcrypto"; -- for gen_random_uuid()

-- ---------------------------------------------------------------------
-- USER
-- No auth system built yet. This table exists so created_by/approved_by
-- have somewhere to point; wire up real auth before relying on it.
-- ---------------------------------------------------------------------
CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    role        TEXT NOT NULL CHECK (role IN ('creator', 'approver')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- EVENT
-- Matches EventInput in backend/app/schemas/content.py. `audience` is
-- free text on purpose — it doubles as the persona-tagging field for
-- Felix's GHL personas without a foreign key into his system.
-- ---------------------------------------------------------------------
CREATE TABLE events (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_by          UUID REFERENCES users(id),
    title               TEXT NOT NULL,
    event_date          DATE NOT NULL,
    event_time          TIME,
    speaker             TEXT,
    registration_link   TEXT,
    audience            TEXT NOT NULL,
    description         TEXT NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- CONTENT_ITEM
-- Central table. One row per generated piece of content.
-- `platform` stays nullable/unused for now — see CLAUDE.md conventions;
-- it exists so a future posting-automation or GHL pipeline doesn't need
-- a migration. `structure_variant` records which structural baseline
-- (see Content Structure Guide) was used, since structure is intentionally
-- flexible, not fixed.
-- ---------------------------------------------------------------------
CREATE TABLE content_items (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id            UUID REFERENCES events(id) ON DELETE CASCADE,
    created_by          UUID REFERENCES users(id),
    approved_by         UUID REFERENCES users(id),
    content_type        TEXT NOT NULL CHECK (
                            content_type IN (
                                'social_post', 'newsletter', 'hashtags', 'image_prompt'
                            )
                        ),
    structure_variant   TEXT,
    platform            TEXT,  -- nullable, future use — see CLAUDE.md
    status              TEXT NOT NULL DEFAULT 'draft' CHECK (
                            status IN ('draft', 'approved', 'published')
                        ),
    body                JSONB NOT NULL,
    scheduled_date      DATE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_content_items_event_id ON content_items(event_id);
CREATE INDEX idx_content_items_status ON content_items(status);
CREATE INDEX idx_content_items_scheduled_date ON content_items(scheduled_date);

-- ---------------------------------------------------------------------
-- KEY_MAKER
-- WVF's 10 client testimonial subjects (per Nancy — distinct from
-- Felix's 4 GHL personas, see Open Questions in PROJECT_CONTEXT.md).
-- Populate with placeholder rows until real details are provided.
-- ---------------------------------------------------------------------
CREATE TABLE key_makers (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                TEXT NOT NULL,
    business_name       TEXT,
    photo_url           TEXT,
    testimonial_quote   TEXT,
    video_link          TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- NEWSLETTER_BLOCK
-- Child of content_items where content_type = 'newsletter'. One row per
-- modular block (feature_article, events_list, grant_flyer, tips_cta,
-- member_spotlight, boilerplate) — see Content Structure Guide.
-- key_maker_id is only set when block_type = 'member_spotlight'.
-- ---------------------------------------------------------------------
CREATE TABLE newsletter_blocks (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_item_id     UUID NOT NULL REFERENCES content_items(id) ON DELETE CASCADE,
    key_maker_id        UUID REFERENCES key_makers(id),
    block_type          TEXT NOT NULL CHECK (
                            block_type IN (
                                'feature_article', 'events_list', 'grant_flyer',
                                'tips_cta', 'member_spotlight', 'boilerplate'
                            )
                        ),
    order_index         INT NOT NULL DEFAULT 0,
    body                JSONB NOT NULL
);

CREATE INDEX idx_newsletter_blocks_content_item_id ON newsletter_blocks(content_item_id);

-- ---------------------------------------------------------------------
-- updated_at trigger for content_items
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_content_items_updated_at
    BEFORE UPDATE ON content_items
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
