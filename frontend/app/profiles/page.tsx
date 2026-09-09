"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { listKeyMakers, type KeyMakerResponse } from "@/lib/api";
import { SideRailPortal } from "@/components/SideRailSlot";

/**
 * Lists WVF's 10 real Key Makers. Limited-info cards by default (photo,
 * business name, owner, type) — clicking one expands it into a full bio
 * panel (title/location/industry/key quotes/story) using a shared-layout
 * (FLIP) transition: the clicked card morphs into the panel and the
 * others dock into a side rail, rather than a hard cut to a new view.
 *
 * Only 4 of the 10 Key Makers have full bio content as of Aug 2026 (see
 * seed_key_makers_public.py) — the other 6 still show "Bio pending" in
 * the expanded panel, never fabricated or left blank.
 */
export default function ProfilesPage() {
  const [keyMakers, setKeyMakers] = useState<KeyMakerResponse[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);

  useEffect(() => {
    listKeyMakers()
      .then(setKeyMakers)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load profiles."));
  }, []);

  const selected = keyMakers?.find((k) => k.id === selectedId) ?? null;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-navy">Key Maker Profiles</h2>
        <p className="text-sm text-gray-600">
          WVF&apos;s Key Makers — client businesses featured in newsletter spotlights. Click a card for
          their full story.
        </p>
      </div>

      {error && (
        <div className="rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {!keyMakers && !error && <p className="text-gray-600">Loading…</p>}

      {keyMakers && keyMakers.length === 0 && (
        <p className="text-gray-600">No Key Makers on file yet.</p>
      )}

      {keyMakers && keyMakers.length > 0 && !selected && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {keyMakers.map((keyMaker) => (
            <KeyMakerCard
              key={keyMaker.id}
              keyMaker={keyMaker}
              collapsed={false}
              active={false}
              onClick={() => setSelectedId(keyMaker.id)}
            />
          ))}
        </div>
      )}

      {/* Once a Key Maker is selected, the full grid above is replaced by
          two things: the collapsed rail (portaled to the window's true
          left edge — see SideRailSlot) and the expanded panel here in the
          normal centered column. */}
      {keyMakers && keyMakers.length > 0 && selected && (
        <>
          <SideRailPortal>
            {/* Horizontal strip below sm, vertical column at sm+ —
                matches side-rail-slot's own mobile layout (see
                RootLayout's comment). */}
            <motion.div
              layout
              className="flex shrink-0 flex-row gap-2 sm:w-14 sm:flex-col"
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
            >
              {keyMakers.map((keyMaker) => (
                <KeyMakerCard
                  key={keyMaker.id}
                  keyMaker={keyMaker}
                  collapsed
                  active={selected.id === keyMaker.id}
                  onClick={() => setSelectedId(keyMaker.id)}
                />
              ))}
            </motion.div>
          </SideRailPortal>

          <AnimatePresence>
            <ExpandedKeyMakerPanel keyMaker={selected} onClose={() => setSelectedId(null)} />
          </AnimatePresence>
        </>
      )}
    </div>
  );
}

function KeyMakerCard({
  keyMaker,
  collapsed,
  active,
  onClick,
}: {
  keyMaker: KeyMakerResponse;
  collapsed: boolean;
  active: boolean;
  onClick: () => void;
}) {
  const [imageFailed, setImageFailed] = useState(false);
  const socialLinks = (keyMaker.social_media ?? "")
    .split(";")
    .map((s) => s.trim())
    .filter(Boolean);
  const initials = keyMaker.business_name
    .split(/\s+/)
    .map((w) => w[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  if (collapsed) {
    // Compact icon-only rail tile — matches a standard tab-rail pattern:
    // just the photo (or initials fallback) in a small square, with an
    // active ring on the currently-expanded Key Maker. No text at this
    // size; the full name/details live in the expanded panel instead.
    return (
      <motion.button
        type="button"
        layoutId={`key-maker-card-${keyMaker.id}`}
        onClick={onClick}
        title={keyMaker.business_name}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className={`flex h-14 w-14 shrink-0 items-center justify-center overflow-hidden rounded-lg border-2 bg-gray-50 shadow-sm transition ${
          active ? "border-navy" : "border-gray-200 hover:border-sky-blue"
        }`}
      >
        {keyMaker.photo_url && !imageFailed ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={keyMaker.photo_url}
            alt={keyMaker.business_name}
            className="h-full w-full object-contain"
            onError={() => setImageFailed(true)}
          />
        ) : (
          <span className="text-sm font-bold text-navy">{initials}</span>
        )}
      </motion.button>
    );
  }

  return (
    <motion.button
      type="button"
      layoutId={`key-maker-card-${keyMaker.id}`}
      onClick={onClick}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
      className="flex h-full w-full flex-col overflow-hidden rounded-lg border border-gray-200 bg-white text-left shadow-sm transition hover:border-sky-blue"
    >
      {/* Always reserve the same h-40 image band, even without a
          working photo (missing photo_url, or a broken URL caught by
          onError) — otherwise a card with no photo collapses to a
          shorter height than its row-mates, misaligning every card in
          that row. object-contain (not cover): sources vary wildly in
          aspect ratio (tall headshots, circular logos, wide banners) —
          cover was cropping people's faces/logos out of frame. */}
      <div className="flex h-40 w-full shrink-0 items-center justify-center bg-gray-50">
        {keyMaker.photo_url && !imageFailed ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={keyMaker.photo_url}
            alt={`${keyMaker.business_name} photo`}
            className="h-full w-full object-contain"
            onError={() => setImageFailed(true)}
          />
        ) : (
          <span className="text-2xl font-bold text-navy">{initials}</span>
        )}
      </div>

      <div className="shrink-0 bg-navy px-5 py-3">
        <h3 className="text-sm font-bold text-white">{keyMaker.business_name}</h3>
        <p className="text-xs text-sky-blue">{keyMaker.owner_name}</p>
      </div>
      <div className="space-y-3 px-5 py-4">
        {keyMaker.business_type && (
          <span className="inline-block rounded-full bg-sky-blue/10 px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wide text-navy">
            {keyMaker.business_type}
          </span>
        )}

        <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">
          {keyMaker.story ? "Click for full story" : "Bio pending"}
        </p>

        {(keyMaker.website || socialLinks.length > 0) && (
          <div className="space-y-1 text-sm">
            {keyMaker.website && <p className="truncate text-sky-blue">{keyMaker.website}</p>}
            {socialLinks.slice(0, 1).map((link) => (
              <p key={link} className="truncate text-gray-600">
                {link}
              </p>
            ))}
          </div>
        )}
      </div>
    </motion.button>
  );
}

function ExpandedKeyMakerPanel({
  keyMaker,
  onClose,
}: {
  keyMaker: KeyMakerResponse;
  onClose: () => void;
}) {
  const [imageFailed, setImageFailed] = useState(false);
  const socialLinks = (keyMaker.social_media ?? "")
    .split(";")
    .map((s) => s.trim())
    .filter(Boolean);

  // Not a shared layoutId with KeyMakerCard: the active card stays visible
  // in the rail too (highlighted, not hidden) while this panel is open, so
  // both are on-screen simultaneously — only one mounted instance of a
  // given layoutId animates correctly, so this uses a plain fade/slide-in
  // instead of morphing from the rail card.
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 8 }}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
      className="flex-1 overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm"
    >
      <div className="flex items-start justify-between gap-4 bg-navy px-6 py-4">
        <div>
          <h3 className="text-lg font-bold text-white">{keyMaker.business_name}</h3>
          <p className="text-sm text-sky-blue">
            {keyMaker.owner_name}
            {keyMaker.title ? ` · ${keyMaker.title}` : ""}
          </p>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Back to all profiles"
          className="shrink-0 rounded-full px-3 py-1 text-sm font-semibold text-white/80 hover:bg-white/10 hover:text-white"
        >
          ← Back
        </button>
      </div>

      <div className="grid grid-cols-1 gap-6 p-6 md:grid-cols-[220px_1fr]">
        <div className="space-y-4">
          {keyMaker.photo_url && !imageFailed && (
            <div className="flex h-56 w-full items-center justify-center rounded-md bg-gray-50">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={keyMaker.photo_url}
                alt={`${keyMaker.business_name} photo`}
                className="h-full w-full object-contain"
                onError={() => setImageFailed(true)}
              />
            </div>
          )}

          <dl className="space-y-2 text-sm">
            {keyMaker.business_type && (
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-gray-500">
                  Business Type
                </dt>
                <dd className="text-gray-800">{keyMaker.business_type}</dd>
              </div>
            )}
            {keyMaker.industry && (
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-gray-500">Industry</dt>
                <dd className="text-gray-800">{keyMaker.industry}</dd>
              </div>
            )}
            {keyMaker.location && (
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-gray-500">Location</dt>
                <dd className="text-gray-800">{keyMaker.location}</dd>
              </div>
            )}
            {keyMaker.website && (
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-gray-500">Website</dt>
                <dd>
                  <a
                    href={keyMaker.website}
                    target="_blank"
                    rel="noreferrer"
                    className="break-all text-sky-blue underline"
                  >
                    {keyMaker.website}
                  </a>
                </dd>
              </div>
            )}
            {socialLinks.length > 0 && (
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-gray-500">Social</dt>
                {socialLinks.map((link) => (
                  <dd key={link} className="text-gray-700">
                    {link}
                  </dd>
                ))}
              </div>
            )}
          </dl>
        </div>

        <div className="space-y-5">
          {keyMaker.key_quotes && keyMaker.key_quotes.length > 0 && (
            <div className="space-y-3">
              {keyMaker.key_quotes.map((quote, i) => (
                <blockquote
                  key={i}
                  className="border-l-4 border-sky-blue bg-sky-blue/5 px-4 py-3 text-sm italic text-navy"
                >
                  “{quote}”
                </blockquote>
              ))}
            </div>
          )}

          {keyMaker.story ? (
            <div className="space-y-3 text-sm leading-relaxed text-gray-700">
              {keyMaker.story.split("\n\n").map((paragraph, i) => (
                <p key={i} className="whitespace-pre-wrap">
                  {paragraph}
                </p>
              ))}
            </div>
          ) : (
            <p className="text-sm italic text-gray-400">
              Bio pending — no full story on file yet for {keyMaker.owner_name}.
            </p>
          )}
        </div>
      </div>
    </motion.div>
  );
}
