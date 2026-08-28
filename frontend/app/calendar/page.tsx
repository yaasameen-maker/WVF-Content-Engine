"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  listEvents,
  listScheduledUnscopedContent,
  type ContentItemResponse,
  type EventWithContentResponse,
} from "@/lib/api";
import { ContentItemDetailModal } from "@/components/ContentItemDetailModal";

/**
 * Content calendar: groups already-generated, persisted content items by
 * their target date. Scoped to social posts and newsletters only for now
 * — flyer/hashtag/calendar-preview items are left out until there's a
 * real destination/workflow decision for them.
 *
 * Two sources are fetched and merged: GET /api/events (content nested
 * under the event it was generated for) and GET /api/content/scheduled
 * (event-less items, e.g. a fixed-template post saved via "Schedule this
 * post" — see ScheduleTemplateButton on the New Campaign page). A given
 * item's date comes from item.scheduled_date when staff set one (see
 * PostDatePicker on the review page / ScheduleTemplateButton), falling
 * back to the parent event's own date otherwise.
 *
 * Two views, matching the WVF SMB/stitch_wvf_content_engine calendar
 * mockup's Month/List toggle: a real month grid (day cells, entries
 * rendered inside their date's cell, prev/next navigation) and a
 * date-grouped list. The mockup's full app shell (Dashboard, Campaigns,
 * Reports, Analytics, AI Insights, dark sidebar) is intentionally not
 * reproduced — see docs/CONTENT_SCOPE.md — only the calendar grid itself.
 *
 * `events.date` is free text (see docs/SCHEMA.sql note on Event), so
 * parsing is best-effort: entries that don't parse to a real date are
 * listed separately rather than silently dropped, in both views.
 * item.scheduled_date is a real ISO "YYYY-MM-DD" string instead, so it's
 * parsed directly rather than through the free-text path.
 */

const SCOPED_CONTENT_TYPES = new Set(["social_post", "newsletter"]);

type ViewMode = "month" | "list";

interface CalendarEntry {
  // Null for event-less items (see GET /api/content/scheduled above).
  event: EventWithContentResponse | null;
  item: ContentItemResponse;
}

interface DayGroup {
  dateKey: string; // yyyy-mm-dd
  label: string;
  items: CalendarEntry[];
}

function parseEventDate(raw: string): Date | null {
  const d = new Date(raw);
  return Number.isNaN(d.getTime()) ? null : d;
}

/** item.scheduled_date is always "YYYY-MM-DD" (see ContentItemResponse),
 * parsed as local calendar values directly rather than through `new
 * Date(iso)`, which reads an unqualified ISO date as UTC midnight and can
 * roll back a day once rendered in a timezone behind UTC. */
function parseScheduledDate(iso: string): Date | null {
  const parts = iso.split("-").map(Number);
  if (parts.length !== 3 || parts.some(Number.isNaN)) return null;
  const [y, m, d] = parts;
  return new Date(y, m - 1, d);
}

function dateKeyOf(d: Date): string {
  // Local-date key (not toISOString, which shifts by timezone offset and
  // can push a date into the wrong day when rendering local grid cells).
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function typeLabel(contentType: string): string {
  return contentType === "social_post" ? "Social" : "Email";
}

function typeStyles(contentType: string): string {
  return contentType === "social_post"
    ? "border-l-4 border-sky-blue bg-sky-blue/10"
    : "border-l-4 border-navy bg-navy/5";
}

export default function CalendarPage() {
  const [events, setEvents] = useState<EventWithContentResponse[] | null>(null);
  const [unscopedItems, setUnscopedItems] = useState<ContentItemResponse[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<ViewMode>("month");
  const [monthCursor, setMonthCursor] = useState(() => {
    const now = new Date();
    return new Date(now.getFullYear(), now.getMonth(), 1);
  });
  const [selected, setSelected] = useState<CalendarEntry | null>(null);

  useEffect(() => {
    listEvents()
      .then(setEvents)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load calendar."));
    listScheduledUnscopedContent()
      .then(setUnscopedItems)
      .catch(() => setUnscopedItems([])); // non-fatal — event-scoped items still show
  }, []);

  const { byDateKey, groupedDays, undated } = useMemo(() => {
    const days = new Map<string, DayGroup>();
    const undatedItems: CalendarEntry[] = [];

    function place(entry: CalendarEntry, dateOverride: Date | null) {
      const parsed = dateOverride ?? (entry.event ? parseEventDate(entry.event.date) : null);
      if (!parsed) {
        undatedItems.push(entry);
        return;
      }

      const dateKey = dateKeyOf(parsed);
      const label = parsed.toLocaleDateString("en-US", {
        weekday: "short",
        month: "short",
        day: "numeric",
      });

      if (!days.has(dateKey)) {
        days.set(dateKey, { dateKey, label, items: [] });
      }
      days.get(dateKey)!.items.push(entry);
    }

    for (const event of events ?? []) {
      for (const item of event.content_items) {
        if (!SCOPED_CONTENT_TYPES.has(item.content_type)) continue;
        // A staff-picked scheduled_date overrides the event's own date
        // (e.g. a reminder post scheduled a few days before the event);
        // falls back to the event date when unset.
        const override = item.scheduled_date ? parseScheduledDate(item.scheduled_date) : null;
        place({ event, item }, override);
      }
    }

    for (const item of unscopedItems ?? []) {
      if (!SCOPED_CONTENT_TYPES.has(item.content_type)) continue;
      const parsed = item.scheduled_date ? parseScheduledDate(item.scheduled_date) : null;
      place({ event: null, item }, parsed);
    }

    const sorted = Array.from(days.values()).sort((a, b) => a.dateKey.localeCompare(b.dateKey));
    return { byDateKey: days, groupedDays: sorted, undated: undatedItems };
  }, [events, unscopedItems]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <h2 className="text-2xl font-bold text-navy">Content Calendar</h2>
          <p className="text-sm text-gray-600">
            Every generated social post and email, grouped by event date.
          </p>
        </div>
        <Link href="/" className="text-sm font-semibold text-sky-blue underline">
          + New campaign
        </Link>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex rounded-lg bg-gray-100 p-1">
          <button
            type="button"
            onClick={() => setView("month")}
            className={`rounded-md px-4 py-1.5 text-sm font-semibold transition ${
              view === "month" ? "bg-white text-navy shadow-sm" : "text-gray-500 hover:text-navy"
            }`}
          >
            Month
          </button>
          <button
            type="button"
            onClick={() => setView("list")}
            className={`rounded-md px-4 py-1.5 text-sm font-semibold transition ${
              view === "list" ? "bg-white text-navy shadow-sm" : "text-gray-500 hover:text-navy"
            }`}
          >
            List
          </button>
        </div>

        {view === "month" && (
          <div className="flex items-center gap-2">
            <button
              type="button"
              aria-label="Previous month"
              onClick={() =>
                setMonthCursor((c) => new Date(c.getFullYear(), c.getMonth() - 1, 1))
              }
              className="rounded-full p-1.5 text-gray-500 hover:bg-gray-100 hover:text-navy"
            >
              ←
            </button>
            <span className="min-w-[140px] text-center text-sm font-semibold text-navy">
              {monthCursor.toLocaleDateString("en-US", { month: "long", year: "numeric" })}
            </span>
            <button
              type="button"
              aria-label="Next month"
              onClick={() =>
                setMonthCursor((c) => new Date(c.getFullYear(), c.getMonth() + 1, 1))
              }
              className="rounded-full p-1.5 text-gray-500 hover:bg-gray-100 hover:text-navy"
            >
              →
            </button>
          </div>
        )}
      </div>

      {error && (
        <div className="rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {!events && !error && <p className="text-gray-600">Loading…</p>}

      {events && groupedDays.length === 0 && undated.length === 0 && (
        <p className="text-gray-600">
          No content yet. Generate a campaign from the event form to see it here.
        </p>
      )}

      {events && view === "month" && (
        <MonthGrid monthCursor={monthCursor} byDateKey={byDateKey} onSelect={setSelected} />
      )}

      {events && view === "list" && (
        <div className="space-y-4">
          {groupedDays.map((day) => (
            <section key={day.dateKey} className="rounded-lg border border-gray-200 shadow-sm">
              <div className="rounded-t-lg bg-navy px-5 py-2.5">
                <h3 className="text-sm font-semibold uppercase tracking-wide text-white">
                  {day.label}
                </h3>
              </div>
              <div className="space-y-2 px-5 py-4">
                {day.items.map(({ event, item }) => (
                  <CalendarItemCard
                    key={item.id}
                    event={event}
                    item={item}
                    onClick={() => setSelected({ event, item })}
                  />
                ))}
              </div>
            </section>
          ))}
        </div>
      )}

      {undated.length > 0 && (
        <section className="rounded-lg border border-gray-200 shadow-sm">
          <div className="rounded-t-lg bg-gray-500 px-5 py-2.5">
            <h3 className="text-sm font-semibold uppercase tracking-wide text-white">
              Date not recognized
            </h3>
          </div>
          <div className="space-y-2 px-5 py-4">
            <p className="mb-2 text-xs text-gray-500">
              These events&apos; date field didn&apos;t parse as a calendar date — check the
              event&apos;s date entry.
            </p>
            {undated.map(({ event, item }) => (
              <CalendarItemCard
                key={item.id}
                event={event}
                item={item}
                showRawDate
                onClick={() => setSelected({ event, item })}
              />
            ))}
          </div>
        </section>
      )}

      {selected && (
        <ContentItemDetailModal
          event={selected.event}
          item={selected.item}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  );
}

const WEEKDAY_LABELS = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];

function MonthGrid({
  monthCursor,
  byDateKey,
  onSelect,
}: {
  monthCursor: Date;
  byDateKey: Map<string, DayGroup>;
  onSelect: (entry: CalendarEntry) => void;
}) {
  const year = monthCursor.getFullYear();
  const month = monthCursor.getMonth();

  const firstOfMonth = new Date(year, month, 1);
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const leadingBlanks = firstOfMonth.getDay(); // 0 = Sunday

  const cells: { date: Date | null; dateKey: string | null }[] = [];
  for (let i = 0; i < leadingBlanks; i++) {
    cells.push({ date: null, dateKey: null });
  }
  for (let day = 1; day <= daysInMonth; day++) {
    const date = new Date(year, month, day);
    cells.push({ date, dateKey: dateKeyOf(date) });
  }
  // Pad to a full last week so the grid ends on a Saturday.
  while (cells.length % 7 !== 0) {
    cells.push({ date: null, dateKey: null });
  }

  const todayKey = dateKeyOf(new Date());

  return (
    <div className="overflow-hidden rounded-lg border border-gray-200 shadow-sm">
      <div className="grid grid-cols-7 border-b border-gray-200 bg-gray-50">
        {WEEKDAY_LABELS.map((label) => (
          <div
            key={label}
            className="py-2 text-center text-xs font-semibold tracking-wide text-gray-500"
          >
            {label}
          </div>
        ))}
      </div>
      <div className="grid grid-cols-7">
        {cells.map((cell, idx) => {
          const isToday = cell.dateKey === todayKey;
          const dayGroup = cell.dateKey ? byDateKey.get(cell.dateKey) : undefined;

          return (
            <div
              key={idx}
              className={`min-h-[110px] border-b border-r border-gray-100 p-2 [&:nth-child(7n)]:border-r-0 ${
                isToday ? "bg-sky-blue/10" : cell.date ? "bg-white" : "bg-gray-50/50"
              }`}
            >
              {cell.date && (
                <>
                  <span
                    className={`text-xs font-semibold ${
                      isToday ? "text-navy" : "text-gray-500"
                    }`}
                  >
                    {cell.date.getDate()}
                  </span>
                  <div className="mt-1 space-y-1">
                    {dayGroup?.items.map(({ event, item }) => (
                      <MonthCellEntry
                        key={item.id}
                        event={event}
                        item={item}
                        onClick={() => onSelect({ event, item })}
                      />
                    ))}
                  </div>
                </>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function MonthCellEntry({
  event,
  item,
  onClick,
}: {
  event: EventWithContentResponse | null;
  item: ContentItemResponse;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`w-full rounded px-1.5 py-1 text-left text-[10px] leading-tight transition hover:brightness-95 ${typeStyles(item.content_type)}`}
    >
      <span className="font-bold uppercase tracking-wide text-navy">{typeLabel(item.content_type)}</span>
      <p className="truncate text-gray-700">
        {event ? event.title : `Scheduled ${item.platform ?? "post"}`}
      </p>
    </button>
  );
}

function CalendarItemCard({
  event,
  item,
  showRawDate = false,
  onClick,
}: {
  event: EventWithContentResponse | null;
  item: ContentItemResponse;
  showRawDate?: boolean;
  onClick: () => void;
}) {
  const bodyPreview =
    item.content_type === "social_post"
      ? (item.body.caption as string | undefined)
      : (item.body.subject_line as string | undefined);

  return (
    <button
      type="button"
      onClick={onClick}
      className={`w-full rounded-md p-3 text-left transition hover:brightness-95 ${typeStyles(item.content_type)}`}
    >
      <div className="mb-1 flex flex-wrap items-center gap-2">
        <span className="rounded-full bg-white px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-navy">
          {typeLabel(item.content_type) === "Social" ? "Social Post" : "Email"}
        </span>
        <span className="rounded-full bg-white px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-gray-500">
          {item.status}
        </span>
        {showRawDate && event && (
          <span className="text-[10px] text-gray-500">raw date: &quot;{event.date}&quot;</span>
        )}
      </div>
      <p className="text-sm font-medium text-gray-800">
        {event ? event.title : `Scheduled ${item.platform ?? "post"}`}
      </p>
      {bodyPreview && <p className="truncate text-xs text-gray-600">{bodyPreview}</p>}
    </button>
  );
}
