"use client";

import { useEffect, useState } from "react";
import { listKeyMakers, type KeyMakerResponse } from "@/lib/api";

/**
 * Lists WVF's 10 real Key Makers with their public profile fields
 * (business name, owner, business type, website, social links).
 *
 * testimonial_quote (bio) is null for every Key Maker as of Aug 2026 — the
 * seed script never populated it, pending real testimonial content from
 * Nancy. Rendered as an explicit "Bio pending" note, never left blank or
 * fabricated. See docs/PROJECT_CONTEXT.md Key Makers open question.
 */
export default function ProfilesPage() {
  const [keyMakers, setKeyMakers] = useState<KeyMakerResponse[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listKeyMakers()
      .then(setKeyMakers)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load profiles."));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-navy">Key Maker Profiles</h2>
        <p className="text-sm text-gray-600">
          WVF&apos;s Key Makers — client businesses featured in newsletter spotlights.
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

      {keyMakers && keyMakers.length > 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {keyMakers.map((keyMaker) => (
            <KeyMakerCard key={keyMaker.id} keyMaker={keyMaker} />
          ))}
        </div>
      )}
    </div>
  );
}

function KeyMakerCard({ keyMaker }: { keyMaker: KeyMakerResponse }) {
  const socialLinks = (keyMaker.social_media ?? "")
    .split(";")
    .map((s) => s.trim())
    .filter(Boolean);

  return (
    <div className="rounded-lg border border-gray-200 shadow-sm">
      <div className="rounded-t-lg bg-navy px-5 py-3">
        <h3 className="text-sm font-bold text-white">{keyMaker.business_name}</h3>
        <p className="text-xs text-sky-blue">{keyMaker.owner_name}</p>
      </div>
      <div className="space-y-3 px-5 py-4">
        {keyMaker.business_type && (
          <span className="inline-block rounded-full bg-sky-blue/10 px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wide text-navy">
            {keyMaker.business_type}
          </span>
        )}

        <div>
          <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-500">Bio</p>
          {keyMaker.testimonial_quote ? (
            <p className="text-sm text-gray-700">{keyMaker.testimonial_quote}</p>
          ) : (
            <p className="text-sm italic text-gray-400">Bio pending — no testimonial on file yet.</p>
          )}
        </div>

        {(keyMaker.website || socialLinks.length > 0) && (
          <div className="space-y-1 text-sm">
            {keyMaker.website && (
              <a
                href={keyMaker.website}
                target="_blank"
                rel="noreferrer"
                className="block truncate text-sky-blue underline"
              >
                {keyMaker.website}
              </a>
            )}
            {socialLinks.map((link) => (
              <p key={link} className="text-gray-600">
                {link}
              </p>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
