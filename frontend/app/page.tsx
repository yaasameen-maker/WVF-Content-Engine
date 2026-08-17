"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { siFacebook, siInstagram, siTiktok, siX } from "simple-icons";
import {
  generateContent,
  getKeymakersStageDetail,
  listKeymakersStages,
  SOCIAL_POST_PLATFORMS,
  type EventInput,
  type KeymakersStageDetail,
  type SocialPostPlatform,
} from "@/lib/api";

const EMPTY_EVENT: EventInput = {
  title: "",
  date: "",
  speaker: "",
  registration_link: "",
  audience: "",
  description: "",
};

const PLATFORM_LABELS: Record<SocialPostPlatform, string> = {
  instagram: "Instagram",
  linkedin: "LinkedIn",
  facebook: "Facebook",
  x: "X",
  tiktok: "TikTok",
};

/** Platforms whose AI Copy style is grounded in real reviewed WVF posts —
 * x/tiktok are deliberately excluded (generic conventions only, no real
 * WVF samples reviewed yet). Drives the wording of the AI Copy sub-note. */
const REAL_SAMPLE_GROUNDED_PLATFORMS: SocialPostPlatform[] = ["instagram", "linkedin", "facebook"];

/** Which tile is selected. "keymakers" shows real WVF reference copy
 * instantly, no AI call. instagram/linkedin/facebook reveal a sub-choice
 * (AI Copy — real today, tailored to that platform's style — or Fixed
 * template — not yet available, no real WVF sample posts exist to show
 * without fabricating content). "ai" reveals the event-form → Generate
 * Campaign flow, platform-agnostic. */
type Mode = SocialPostPlatform | "keymakers" | "ai" | null;

/** Once a platform tile is selected, which of the two sub-options (if
 * any) is active. Reset whenever the platform tile changes. */
type PlatformSubMode = "ai" | "fixed" | null;

export default function EventFormPage() {
  const router = useRouter();
  const [event, setEvent] = useState<EventInput>(EMPTY_EVENT);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  const [mode, setMode] = useState<Mode>(null);
  const [platformSubMode, setPlatformSubMode] = useState<PlatformSubMode>(null);

  const [keymakersStages, setKeymakersStages] = useState<Record<string, string> | null>(null);
  const [keymakersStageKey, setKeymakersStageKey] = useState("");
  const [keymakersDetail, setKeymakersDetail] = useState<KeymakersStageDetail | null>(null);
  const [keymakersDetailError, setKeymakersDetailError] = useState<string | null>(null);

  useEffect(() => {
    listKeymakersStages()
      .then((stages) => {
        setKeymakersStages(stages);
        const firstKey = Object.keys(stages)[0];
        if (firstKey) setKeymakersStageKey(firstKey);
      })
      .catch(() => {
        // Non-fatal: the tile just won't be usable if this fails (e.g.
        // backend not running). AI generation still works independently.
        setKeymakersStages({});
      });
  }, []);

  // Fetch the real static copy for the selected Keymakers stage whenever
  // the tile is active and a stage is chosen — this is instant reference
  // content, not an AI generation call.
  useEffect(() => {
    if (mode !== "keymakers" || !keymakersStageKey) return;
    setKeymakersDetailError(null);
    getKeymakersStageDetail(keymakersStageKey)
      .then(setKeymakersDetail)
      .catch((err) =>
        setKeymakersDetailError(err instanceof Error ? err.message : "Failed to load this message.")
      );
  }, [mode, keymakersStageKey]);

  function updateField(field: keyof EventInput, value: string) {
    setEvent((prev) => ({ ...prev, [field]: value }));
  }

  function selectMode(next: Mode) {
    setMode((prev) => (prev === next ? null : next));
    setPlatformSubMode(null);
    setShowForm(false);
  }

  const activePlatform: SocialPostPlatform | null =
    mode && (SOCIAL_POST_PLATFORMS as readonly string[]).includes(mode)
      ? (mode as SocialPostPlatform)
      : null;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setIsGenerating(true);

    try {
      const result = await generateContent(
        event,
        activePlatform ? { socialPostPlatform: activePlatform } : undefined
      );
      sessionStorage.setItem("wvf_generated_content", JSON.stringify(result));
      sessionStorage.setItem("wvf_source_event", JSON.stringify(event));
      sessionStorage.removeItem("wvf_keymakers_stage_label");
      if (activePlatform) {
        sessionStorage.setItem("wvf_social_post_platform_label", PLATFORM_LABELS[activePlatform]);
      } else {
        sessionStorage.removeItem("wvf_social_post_platform_label");
      }
      router.push("/review");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong generating content.");
    } finally {
      setIsGenerating(false);
    }
  }

  const keymakersDisabled = !keymakersStages || Object.keys(keymakersStages).length === 0;

  return (
    <div>
      <InstagramGradientDef />
      <div className="mb-6">
        <span className="mb-2 block text-sm font-medium text-navy">
          Choose a real WVF template, or use AI to generate new copy
        </span>
        <div className="flex flex-wrap gap-3">
          <PlatformToggleButton
            label="Instagram"
            active={mode === "instagram"}
            onClick={() => selectMode("instagram")}
            icon={<BrandSvgIcon icon={siInstagram} fill={`url(#${IG_GRADIENT_ID})`} />}
          />
          <PlatformToggleButton
            label="LinkedIn"
            active={mode === "linkedin"}
            onClick={() => selectMode("linkedin")}
            icon={<LinkedInMonogramIcon />}
          />
          <PlatformToggleButton
            label="Facebook"
            active={mode === "facebook"}
            onClick={() => selectMode("facebook")}
            icon={<BrandSvgIcon icon={siFacebook} fill={`#${siFacebook.hex}`} />}
          />
          <PlatformToggleButton
            label="X"
            active={mode === "x"}
            onClick={() => selectMode("x")}
            icon={<BrandSvgIcon icon={siX} fill={mode === "x" ? "#FFFFFF" : `#${siX.hex}`} />}
          />
          <PlatformToggleButton
            label="TikTok"
            active={mode === "tiktok"}
            onClick={() => selectMode("tiktok")}
            icon={
              <BrandSvgIcon icon={siTiktok} fill={mode === "tiktok" ? "#FFFFFF" : `#${siTiktok.hex}`} />
            }
          />
          <PlatformToggleButton
            label="Keymakers Copy"
            active={mode === "keymakers"}
            onClick={() => selectMode("keymakers")}
            disabled={keymakersDisabled}
            icon={
              // eslint-disable-next-line @next/next/no-img-element
              <img src="/wvf-logo.svg" alt="" className="h-16 w-auto max-w-none" />
            }
          />
          <PlatformToggleButton
            label="AI Copy"
            active={mode === "ai"}
            onClick={() => selectMode("ai")}
            icon={<AiSparkleIcon />}
          />
        </div>

        {activePlatform && (
          <div className="mt-4 max-w-xl">
            <span className="mb-2 block text-sm font-medium text-navy">
              {PLATFORM_LABELS[activePlatform]}: how do you want to start?
            </span>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => {
                  setPlatformSubMode("ai");
                  setShowForm(false);
                }}
                className={`rounded-md border-2 px-4 py-2 text-sm font-semibold transition ${
                  platformSubMode === "ai"
                    ? "border-navy bg-navy text-white"
                    : "border-gray-200 bg-white text-gray-600 hover:border-sky-blue hover:text-navy"
                }`}
              >
                AI Copy
              </button>
              <button
                type="button"
                onClick={() => {
                  setPlatformSubMode("fixed");
                  setShowForm(false);
                }}
                className={`rounded-md border-2 px-4 py-2 text-sm font-semibold transition ${
                  platformSubMode === "fixed"
                    ? "border-navy bg-navy text-white"
                    : "border-gray-200 bg-white text-gray-600 hover:border-sky-blue hover:text-navy"
                }`}
              >
                Fixed template
              </button>
            </div>

            {platformSubMode === "ai" && (
              <p className="mt-2 text-xs text-gray-500">
                {REAL_SAMPLE_GROUNDED_PLATFORMS.includes(activePlatform)
                  ? `Social post caption will be tailored to ${PLATFORM_LABELS[activePlatform]}'s real WVF style (grounded in real WVF posts).`
                  : `Social post caption will follow general ${PLATFORM_LABELS[activePlatform]} conventions — not yet grounded in real WVF ${PLATFORM_LABELS[activePlatform]} posts, since none have been reviewed for this platform.`}
                {" "}Fill in event details below and click Generate Campaign.
              </p>
            )}

            {platformSubMode === "fixed" && (
              <div className="mt-2 rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                A fixed (non-AI) {PLATFORM_LABELS[activePlatform]} template isn&apos;t available yet —
                real sample WVF {PLATFORM_LABELS[activePlatform]} posts are needed to build one, so this
                doesn&apos;t show fabricated content in WVF&apos;s name. Use AI Copy in the meantime.
              </div>
            )}
          </div>
        )}

        {mode === "keymakers" && (
          <div className="mt-4 max-w-2xl">
            <span className="mb-1 block text-sm font-medium text-navy">Which Keymakers message?</span>
            <select
              value={keymakersStageKey}
              onChange={(e) => setKeymakersStageKey(e.target.value)}
              className="input"
            >
              {Object.entries(keymakersStages ?? {}).map(([key, label]) => (
                <option key={key} value={key}>
                  {label}
                </option>
              ))}
            </select>

            {keymakersDetailError && (
              <div className="mt-3 rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
                {keymakersDetailError}
              </div>
            )}

            {keymakersDetail && !keymakersDetailError && (
              <div className="mt-3 rounded-lg border border-gray-200 shadow-sm">
                <div className="rounded-t-lg bg-navy px-5 py-3">
                  <h3 className="font-semibold text-white">{keymakersDetail.label}</h3>
                </div>
                <div className="space-y-3 px-5 py-4">
                  <p className="text-xs text-gray-500">
                    Audience: {keymakersDetail.audience}
                    {keymakersDetail.subject_options && keymakersDetail.subject_options.length > 0 && (
                      <>
                        <br />
                        Subject line options: {keymakersDetail.subject_options.join(" · ")}
                      </>
                    )}
                  </p>
                  <pre className="whitespace-pre-wrap font-sans text-sm text-gray-800">
                    {keymakersDetail.body}
                  </pre>
                  <p className="text-xs font-semibold text-amber-700">
                    Real WVF reference copy — still needs Maria&apos;s approval before sending.
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {(mode === "ai" || platformSubMode === "ai") && !showForm && (
        <button
          type="button"
          onClick={() => setShowForm(true)}
          className="rounded-md bg-navy px-6 py-3 font-semibold text-white transition hover:bg-navy/90"
        >
          + New Event Campaign
        </button>
      )}

      {(mode === "ai" || platformSubMode === "ai") && showForm && (
        <>
          <div className="mb-1 flex items-center justify-between">
            <h2 className="text-2xl font-bold text-navy">New Event Campaign</h2>
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="text-sm font-semibold text-gray-500 hover:text-navy"
            >
              Cancel
            </button>
          </div>
          <p className="mb-6 text-sm text-gray-600">
            Enter event details to generate a complete WVF-branded marketing campaign.
          </p>

          <form onSubmit={handleSubmit} className="space-y-5">
            <Field label="Event Title">
              <input
                required
                type="text"
                value={event.title}
                onChange={(e) => updateField("title", e.target.value)}
                className="input"
                placeholder="Money & Credit: Understanding Your Credit Report"
              />
            </Field>

            <Field label="Date">
              <input
                required
                type="text"
                value={event.date}
                onChange={(e) => updateField("date", e.target.value)}
                className="input"
                placeholder="August 15, 2026 at 2:00 PM ET"
              />
            </Field>

            <Field label="Speaker">
              <input
                required
                type="text"
                value={event.speaker}
                onChange={(e) => updateField("speaker", e.target.value)}
                className="input"
                placeholder="WVF Financial Education Team"
              />
            </Field>

            <Field label="Registration Link">
              <input
                required
                type="url"
                value={event.registration_link}
                onChange={(e) => updateField("registration_link", e.target.value)}
                className="input"
                placeholder="https://www.womenventurefund.org/events/..."
              />
            </Field>

            <Field label="Target Audience">
              <input
                required
                type="text"
                value={event.audience}
                onChange={(e) => updateField("audience", e.target.value)}
                className="input"
                placeholder="NYC-based women entrepreneurs, Spanish-speaking community welcome"
              />
            </Field>

            <Field label="Description">
              <textarea
                required
                rows={5}
                value={event.description}
                onChange={(e) => updateField("description", e.target.value)}
                className="input"
                placeholder="Describe the event, what attendees will learn, and any relevant details..."
              />
            </Field>

            {error && (
              <div className="rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isGenerating}
              className="rounded-md bg-navy px-6 py-3 font-semibold text-white transition hover:bg-navy/90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isGenerating ? "Generating campaign…" : "Generate Campaign"}
            </button>
          </form>
        </>
      )}

      <style jsx global>{`
        .input {
          width: 100%;
          border: 1px solid #d1d5db;
          border-radius: 0.375rem;
          padding: 0.5rem 0.75rem;
          font-size: 0.95rem;
        }
        .input:focus {
          outline: none;
          border-color: #6fa8dc;
          box-shadow: 0 0 0 2px rgba(111, 168, 220, 0.3);
        }
      `}</style>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-navy">{label}</span>
      {children}
    </label>
  );
}

function PlatformToggleButton({
  label,
  icon,
  active,
  disabled,
  onClick,
}: {
  label: string;
  icon: React.ReactNode;
  active: boolean;
  disabled?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-pressed={active}
      className={`flex flex-col items-center gap-3 rounded-xl border-2 px-9 py-6 text-base font-semibold transition disabled:cursor-not-allowed disabled:opacity-40 ${
        active
          ? "border-navy bg-navy text-white"
          : "border-gray-200 bg-white text-gray-600 hover:border-sky-blue hover:text-navy"
      }`}
    >
      <span className="flex h-14 w-14 items-center justify-center">{icon}</span>
      {label}
    </button>
  );
}

/** Renders a simple-icons brand icon (real, properly-licensed SVG path
 * data — see simple-icons npm package, CC0/MIT licensed) at a fixed size,
 * filled with the brand's own real color rather than `currentColor`, so
 * it always reads in-brand regardless of the toggle button's
 * active/inactive state. `fill` accepts either a flat hex or a gradient
 * url(#id) reference — see IG_GRADIENT_ID below. */
function BrandSvgIcon({
  icon,
  fill,
}: {
  icon: { path: string; title: string };
  fill: string;
}) {
  return (
    <svg viewBox="0 0 24 24" role="img" aria-label={icon.title} className="h-14 w-14" fill={fill}>
      <path d={icon.path} />
    </svg>
  );
}

const IG_GRADIENT_ID = "ig-brand-gradient";

/** Instagram's real mark is a gradient, not a flat color — simple-icons
 * only ships a flat brand hex, so this defines the actual Instagram
 * gradient stops (per Instagram's own brand assets) once, referenced by
 * the Instagram <BrandSvgIcon> via fill="url(#ig-brand-gradient)". Must
 * render once per page, not once per icon instance. */
function InstagramGradientDef() {
  return (
    <svg width="0" height="0" className="absolute" aria-hidden="true">
      <defs>
        <linearGradient id={IG_GRADIENT_ID} x1="0%" y1="100%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#FEDA75" />
          <stop offset="25%" stopColor="#FA7E1E" />
          <stop offset="50%" stopColor="#D62976" />
          <stop offset="75%" stopColor="#962FBF" />
          <stop offset="100%" stopColor="#4F5BD5" />
        </linearGradient>
      </defs>
    </svg>
  );
}

/** LinkedIn has no icon in the installed simple-icons version (removed
 * from the package — see LinkedIn's own trademark enforcement history).
 * Rather than fabricate an inaccurate logo shape from memory, this is a
 * plain generic "in" monogram on LinkedIn's real brand blue (#0A66C2) —
 * not LinkedIn's real mark, but in its real color. Uses an inline color
 * (not the `text-white` class) so the letterform renders true #FFFFFF,
 * not a washed-out gray from anti-aliasing at small sizes. */
function LinkedInMonogramIcon() {
  return (
    <span
      aria-label="LinkedIn"
      style={{ backgroundColor: "#0A66C2", color: "#FFFFFF" }}
      className="flex h-14 w-14 items-center justify-center rounded-lg text-2xl font-bold leading-none"
    >
      in
    </span>
  );
}

/** Simple sparkle glyph marking the AI-generation tile — not a brand mark,
 * just a plain hand-drawn shape in the WVF sky-blue so it doesn't compete
 * visually with the real brand icons beside it. */
function AiSparkleIcon() {
  return (
    <svg viewBox="0 0 24 24" role="img" aria-label="AI Copy" className="h-14 w-14" fill="#6FA8DC">
      <path d="M12 2l1.8 5.2L19 9l-5.2 1.8L12 16l-1.8-5.2L5 9l5.2-1.8L12 2z" />
      <path d="M19 14l.9 2.6L22.5 17.5l-2.6.9L19 21l-.9-2.6-2.6-.9 2.6-.9L19 14z" />
    </svg>
  );
}
