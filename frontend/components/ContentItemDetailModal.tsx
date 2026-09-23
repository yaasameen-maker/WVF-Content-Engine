"use client";

import { useEffect, useState } from "react";
import {
  deleteContentItem,
  updateContentItemBody,
  type ContentItemResponse,
  type EventWithContentResponse,
} from "@/lib/api";
import { ApproveButton } from "@/components/ApproveButton";
import { PhotoTextComposer } from "@/components/PhotoTextComposer";
import { PostToXButton } from "@/components/PostToXButton";

/**
 * Full detail popup for a single planned/generated content item, opened by
 * clicking an entry on the Calendar page. Shows every real field that
 * exists on the item today.
 *
 * Includes the real Approve and Post to X actions (Sept 2026) — this
 * used to be the only place content lives that has NO path to approval
 * or manual posting at all: both actions previously only existed on the
 * review page right after generating, before navigating away, so
 * anything saved via "Schedule this post" (a fixed template, never
 * generated through /review) had no way to ever be approved or posted.
 * Both only shown for social_post items, matching the review page —
 * other content types don't have approve/post flows built yet.
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
  onDeleted,
}: {
  // Null for items with no source event — e.g. a fixed-template post
  // scheduled via POST /api/content/schedule-template, which has no
  // event form behind it at all.
  event: EventWithContentResponse | null;
  item: ContentItemResponse;
  onClose: () => void;
  // Called after a successful delete so the calendar can drop this item
  // from its in-memory lists without a full refetch.
  onDeleted?: (contentItemId: number) => void;
}) {
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // Editing a not-yet-published social_post's caption/hashtags/CTA
  // directly from the calendar — previously the only editor for saved
  // content was the review page right after generating, so anything
  // reached via /calendar (e.g. days later, or a "Schedule this post"
  // template with no /review step at all) had no way to fix a typo or
  // tweak copy before it went out. `body` tracks the current edited
  // values; it's what gets PATCHed on Save and what's passed to
  // PostToXButton, so "Post to X" always sends what's on screen rather
  // than the original saved body if edits haven't been saved yet.
  const [isEditing, setIsEditing] = useState(false);
  const [body, setBody] = useState(item.body);
  const [savingEdit, setSavingEdit] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);

  const canEdit = item.content_type === "social_post" && item.status !== "published";

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  async function handleDelete() {
    setDeleting(true);
    setDeleteError(null);
    try {
      await deleteContentItem(item.id);
      onDeleted?.(item.id);
      onClose();
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : "Failed to delete.");
      setDeleting(false);
    }
  }

  async function handleSaveEdit() {
    setSavingEdit(true);
    setEditError(null);
    try {
      const updated = await updateContentItemBody(item.id, body);
      setBody(updated.body);
      setIsEditing(false);
    } catch (err) {
      setEditError(err instanceof Error ? err.message : "Failed to save changes.");
    } finally {
      setSavingEdit(false);
    }
  }

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
            <DetailField label={item.scheduled_date ? "Scheduled Date" : "Event Date"}>
              {item.scheduled_date
                ? `${item.scheduled_date}${item.scheduled_time ? ` at ${item.scheduled_time}` : ""}`
                : event
                  ? event.date || "—"
                  : "—"}
            </DetailField>
            <DetailField label="Platform">{item.platform ?? "—"}</DetailField>
            <DetailField label="Structure Variant">{item.structure_variant ?? "—"}</DetailField>
            <DetailField label="Created">{formatTimestamp(item.created_at)}</DetailField>
            <DetailField label="Last Updated">{formatTimestamp(item.updated_at)}</DetailField>
          </dl>

          {item.is_stale && (
            <div className="rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-800">
              <span className="font-semibold">Scheduled time passed — not auto-posted.</span> This
              was approved more than 72 hours after its scheduled date/time, so automatic posting
              skipped it. It&apos;s still approved — use &quot;Post to X&quot; below if you still
              want to send it.
            </div>
          )}

          {item.content_type === "social_post" && (
            <div className="space-y-3">
              <div>
                <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-500">
                  Approval
                </p>
                <ApproveButton
                  contentItemId={item.id}
                  initialStatus={item.status}
                  initialApprovedByName={item.approved_by_name}
                />
              </div>
              <PostToXButton contentItemId={item.id} currentBody={body} />
            </div>
          )}

          {canEdit && !isEditing && (
            <button
              type="button"
              onClick={() => setIsEditing(true)}
              className="text-xs font-semibold text-sky-blue underline"
            >
              Edit caption/hashtags/image
            </button>
          )}

          {canEdit && isEditing ? (
            <>
              <EditableSocialPostBody
                body={body}
                onChange={setBody}
                onSave={handleSaveEdit}
                onCancel={() => {
                  setBody(item.body);
                  setEditError(null);
                  setIsEditing(false);
                }}
                saving={savingEdit}
                error={editError}
              />
              {/* Same composer the review page uses right after
                  generating — building here overwrites/creates this
                  item's composed image, same as there. Nothing viewed
                  via /calendar previously had any way to touch the
                  image at all once past that first /review step. */}
              <PhotoTextComposer
                contentItemId={item.id}
                initialText={(body.caption as string | undefined) ?? ""}
              />
            </>
          ) : (
            <ContentBody item={{ ...item, body }} />
          )}

          <div className="border-t border-gray-100 pt-4">
            {item.status === "published" ? (
              <p className="text-xs text-gray-500">
                This item has already been published and can&apos;t be deleted from the calendar.
              </p>
            ) : deleteError ? (
              <div className="space-y-2">
                <p className="text-sm text-red-600">{deleteError}</p>
                <button
                  type="button"
                  onClick={() => setDeleteError(null)}
                  className="text-xs font-semibold text-gray-500 underline"
                >
                  Dismiss
                </button>
              </div>
            ) : confirmingDelete ? (
              <div className="flex flex-wrap items-center gap-3">
                <span className="text-sm text-gray-700">Delete this scheduled post?</span>
                <button
                  type="button"
                  onClick={handleDelete}
                  disabled={deleting}
                  className="rounded-md bg-red-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-red-700 disabled:opacity-50"
                >
                  {deleting ? "Deleting…" : "Yes, delete"}
                </button>
                <button
                  type="button"
                  onClick={() => setConfirmingDelete(false)}
                  disabled={deleting}
                  className="text-xs font-semibold text-gray-500 underline disabled:opacity-50"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => setConfirmingDelete(true)}
                className="text-xs font-semibold text-red-600 underline"
              >
                Delete from calendar
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/** Editable caption/hashtags/CTA form for a not-yet-published social_post
 * — shown instead of ContentBody's read-only view while isEditing is
 * true (see ContentItemDetailModal.canEdit). Hashtags are edited as a
 * single space-separated string, same convention as the review page's
 * template editors (see EditableTemplatePreview on the homepage), then
 * split back into an array on save. */
function EditableSocialPostBody({
  body,
  onChange,
  onSave,
  onCancel,
  saving,
  error,
}: {
  body: Record<string, unknown>;
  onChange: (body: Record<string, unknown>) => void;
  onSave: () => void;
  onCancel: () => void;
  saving: boolean;
  error: string | null;
}) {
  const caption = (body.caption as string | undefined) ?? "";
  const hashtagsText = Array.isArray(body.hashtags) ? (body.hashtags as string[]).join(" ") : "";
  const cta = (body.cta as string | undefined) ?? "";

  function setField(field: string, value: unknown) {
    onChange({ ...body, [field]: value });
  }

  return (
    <div className="space-y-3 border-t border-gray-100 pt-4">
      <label className="block">
        <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-gray-500">
          Caption
        </span>
        <textarea
          rows={5}
          value={caption}
          onChange={(e) => setField("caption", e.target.value)}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
        />
      </label>
      <label className="block">
        <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-gray-500">
          Hashtags (space-separated)
        </span>
        <input
          type="text"
          value={hashtagsText}
          onChange={(e) =>
            setField(
              "hashtags",
              e.target.value
                .split(/\s+/)
                .map((h) => h.trim())
                .filter(Boolean)
            )
          }
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
        />
      </label>
      <label className="block">
        <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-gray-500">
          Call to Action
        </span>
        <input
          type="text"
          value={cta}
          onChange={(e) => setField("cta", e.target.value)}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
        />
      </label>

      {error && (
        <div className="rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onSave}
          disabled={saving}
          className="rounded-md bg-navy px-4 py-2 text-sm font-semibold text-white transition hover:bg-navy/90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {saving ? "Saving…" : "Save changes"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={saving}
          className="text-xs font-semibold text-gray-500 underline disabled:opacity-50"
        >
          Cancel
        </button>
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
