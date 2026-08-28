"use client";

import { useEffect } from "react";
import type { ContentItemResponse, EventWithContentResponse } from "@/lib/api";

/**
 * Full detail popup for a single planned/generated content item, opened by
 * clicking an entry on the Calendar page. Shows every real field that
 * exists on the item today.
 *
 * "Who approved it" is intentionally NOT shown as a name — there is no
 * auth/user system built yet (see CLAUDE.md Status: "Auth/user system not
 * built — users.role exists in schema, no login yet"), so ContentItem has
 * no approved_by column. Only `status` (draft/approved/published) and
 * `updated_at` are real. Showing a fabricated approver name here would be
 * worse than admitting the gap.
 */

const STATUS_STYLES: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700",
  approved: "bg-green-100 text-green-700",
  published: "bg-sky-blue/20 text-navy",
};

function contentTypeLabel(contentType: string): string {
  switch (contentType) {
    case "social_post":
      return "Social Post";
    case "hashtags":
      return "Hashtags";
    case "newsletter":
      return "Newsletter";
    case "flyer":
      return "Flyer";
    case "newsletter_block":
      return "Newsletter Block";
    default:
      return contentType;
  }
}

function formatTimestamp(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function ContentItemDetailModal({
  event,
  item,
  onClose,
}: {
  // Null for items with no source event — e.g. a fixed-template post
  // scheduled via POST /api/content/schedule-template, which has no
  // event form behind it at all.
  event: EventWithContentResponse | null;
  item: ContentItemResponse;
  onClose: () => void;
}) {
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4 py-8"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        className="max-h-full w-full max-w-lg overflow-y-auto rounded-lg bg-white shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4 rounded-t-lg bg-navy px-5 py-4">
          <div>
            <span className="mb-1 inline-block rounded-full bg-white/15 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-white">
              {contentTypeLabel(item.content_type)}
            </span>
            <h3 className="text-base font-bold text-white">
              {event ? event.title : "Scheduled template post"}
            </h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="shrink-0 rounded-full p-1 text-white/80 hover:bg-white/10 hover:text-white"
          >
            ✕
          </button>
        </div>

        <div className="space-y-4 px-5 py-4">
          <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
            <DetailField label="Status">
              <span
                className={`inline-block rounded-full px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide ${
                  STATUS_STYLES[item.status] ?? "bg-gray-100 text-gray-700"
                }`}
              >
                {item.status}
              </span>
            </DetailField>
            <DetailField label={event ? "Event Date" : "Scheduled Date"}>
              {event ? event.date || "—" : item.scheduled_date || "—"}
            </DetailField>
            <DetailField label="Platform">{item.platform ?? "—"}</DetailField>
            <DetailField label="Structure Variant">{item.structure_variant ?? "—"}</DetailField>
            <DetailField label="Created">{formatTimestamp(item.created_at)}</DetailField>
            <DetailField label="Last Updated">{formatTimestamp(item.updated_at)}</DetailField>
          </dl>

          <div>
            <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-500">
              Approved By
            </p>
            <p className="text-sm italic text-gray-400">
              Not available — WVF Content Engine has no login/approver tracking yet. Status above
              reflects the last known review state.
            </p>
          </div>

          <ContentBody item={item} />
        </div>
      </div>
    </div>
  );
}

function DetailField({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs font-semibold uppercase tracking-wide text-gray-500">{label}</dt>
      <dd className="mt-0.5 text-gray-800">{children}</dd>
    </div>
  );
}

function ContentBody({ item }: { item: ContentItemResponse }) {
  const body = item.body;

  if (item.content_type === "social_post") {
    return (
      <div className="space-y-3 border-t border-gray-100 pt-4">
        <BodyBlock label="Caption" value={body.caption as string | undefined} />
        <BodyBlock
          label="Hashtags"
          value={Array.isArray(body.hashtags) ? (body.hashtags as string[]).join(" ") : undefined}
          accent
        />
        <BodyBlock label="Call to Action" value={body.cta as string | undefined} />
        <BodyBlock
          label="Suggested Image Prompt"
          value={body.suggested_image_prompt as string | undefined}
          italic
        />
      </div>
    );
  }

  if (item.content_type === "hashtags") {
    return (
      <div className="space-y-3 border-t border-gray-100 pt-4">
        <BodyBlock
          label="Primary Hashtags"
          value={
            Array.isArray(body.primary_hashtags)
              ? (body.primary_hashtags as string[]).join(" ")
              : undefined
          }
          accent
        />
        <BodyBlock
          label="Topic Hashtags"
          value={
            Array.isArray(body.topic_hashtags) ? (body.topic_hashtags as string[]).join(" ") : undefined
          }
          accent
        />
        <BodyBlock label="Rationale" value={body.rationale as string | undefined} italic />
      </div>
    );
  }

  if (item.content_type === "newsletter") {
    return (
      <div className="space-y-3 border-t border-gray-100 pt-4">
        <BodyBlock label="Subject Line" value={body.subject_line as string | undefined} />
        <BodyBlock label="Preview Text" value={body.preview_text as string | undefined} />
        <BodyBlock label="Body" value={body.body_plain_text as string | undefined} />
        <BodyBlock label="Call to Action" value={body.cta_text as string | undefined} />
      </div>
    );
  }

  if (item.content_type === "flyer") {
    return (
      <div className="space-y-3 border-t border-gray-100 pt-4">
        <BodyBlock label="Headline" value={body.headline as string | undefined} />
        <BodyBlock label="Subheadline" value={body.subheadline as string | undefined} />
        <BodyBlock label="Body" value={body.body as string | undefined} />
        <BodyBlock label="Call to Action" value={body.cta as string | undefined} />
        <BodyBlock label="Footer Details" value={body.footer_details as string | undefined} italic />
      </div>
    );
  }

  // Fallback for newsletter_block and anything else — show raw fields.
  return (
    <div className="space-y-2 border-t border-gray-100 pt-4">
      {Object.entries(body).map(([key, value]) => (
        <BodyBlock
          key={key}
          label={key.replace(/_/g, " ")}
          value={typeof value === "string" ? value : JSON.stringify(value)}
        />
      ))}
    </div>
  );
}

function BodyBlock({
  label,
  value,
  accent = false,
  italic = false,
}: {
  label: string;
  value: string | undefined;
  accent?: boolean;
  italic?: boolean;
}) {
  if (!value) return null;
  return (
    <div>
      <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-500">{label}</p>
      <p
        className={`whitespace-pre-wrap text-sm ${accent ? "text-sky-blue" : "text-gray-800"} ${
          italic ? "italic text-gray-600" : ""
        }`}
      >
        {value}
      </p>
    </div>
  );
}
