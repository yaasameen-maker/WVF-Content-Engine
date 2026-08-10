"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { siFacebook, siInstagram } from "simple-icons";
import {
  generateContent,
  listKeymakersStages,
  SOCIAL_POST_PLATFORMS,
  type EventInput,
  type SocialPostPlatform,
} from "@/lib/api";

const PLATFORM_LABELS: Record<SocialPostPlatform, string> = {
  instagram: "Instagram",
  linkedin: "LinkedIn",
  facebook: "Facebook",
};

const EMPTY_EVENT: EventInput = {
  title: "",
  date: "",
  speaker: "",
  registration_link: "",
  audience: "",
  description: "",
};

export default function EventFormPage() {
  const router = useRouter();
  const [event, setEvent] = useState<EventInput>(EMPTY_EVENT);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [socialPostPlatform, setSocialPostPlatform] = useState<SocialPostPlatform | "">("");

  const [useKeymakersCopy, setUseKeymakersCopy] = useState(false);
  const [keymakersStages, setKeymakersStages] = useState<Record<string, string> | null>(null);
  const [keymakersStageKey, setKeymakersStageKey] = useState("");

  useEffect(() => {
    listKeymakersStages()
      .then((stages) => {
        setKeymakersStages(stages);
        const firstKey = Object.keys(stages)[0];
        if (firstKey) setKeymakersStageKey(firstKey);
      })
      .catch(() => {
        // Non-fatal: the toggle just won't be usable if this fails
        // (e.g. backend not running). Normal event generation still works.
        setKeymakersStages({});
      });
  }, []);

  function updateField(field: keyof EventInput, value: string) {
    setEvent((prev) => ({ ...prev, [field]: value }));
  }

  function togglePlatform(platform: SocialPostPlatform) {
    setSocialPostPlatform((prev) => (prev === platform ? "" : platform));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setIsGenerating(true);

    try {
      const activeKeymakersStage = useKeymakersCopy && keymakersStageKey ? keymakersStageKey : null;
      const result = await generateContent(event, {
        ...(activeKeymakersStage ? { keymakersStageKey: activeKeymakersStage } : {}),
        ...(socialPostPlatform ? { socialPostPlatform } : {}),
      });
      sessionStorage.setItem("wvf_generated_content", JSON.stringify(result));
      sessionStorage.setItem("wvf_source_event", JSON.stringify(event));
      if (activeKeymakersStage) {
        sessionStorage.setItem("wvf_keymakers_stage_label", keymakersStages?.[activeKeymakersStage] ?? activeKeymakersStage);
      } else {
        sessionStorage.removeItem("wvf_keymakers_stage_label");
      }
      if (socialPostPlatform) {
        sessionStorage.setItem("wvf_social_post_platform_label", PLATFORM_LABELS[socialPostPlatform]);
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
      <h2 className="mb-1 text-2xl font-bold text-navy">New Event Campaign</h2>
      <p className="mb-6 text-sm text-gray-600">
        Enter event details to generate a complete WVF-branded marketing campaign.
      </p>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <span className="mb-2 block text-sm font-medium text-navy">
            Tailor the social post for a platform, or generate Keymakers recruitment copy
            <span className="ml-1 font-normal text-gray-500">(optional — leave all off for a normal rotating post)</span>
          </span>
          <div className="flex flex-wrap gap-3">
            <PlatformToggleButton
              label="Instagram"
              active={socialPostPlatform === "instagram"}
              onClick={() => togglePlatform("instagram")}
              icon={<BrandSvgIcon icon={siInstagram} />}
            />
            <PlatformToggleButton
              label="LinkedIn"
              active={socialPostPlatform === "linkedin"}
              onClick={() => togglePlatform("linkedin")}
              icon={<LinkedInMonogramIcon />}
            />
            <PlatformToggleButton
              label="Facebook"
              active={socialPostPlatform === "facebook"}
              onClick={() => togglePlatform("facebook")}
              icon={<BrandSvgIcon icon={siFacebook} />}
            />
            <PlatformToggleButton
              label="Keymakers Copy"
              active={useKeymakersCopy}
              onClick={() => setUseKeymakersCopy((v) => !v)}
              disabled={keymakersDisabled}
              icon={
                // eslint-disable-next-line @next/next/no-img-element
                <img src="/wvf-logo.svg" alt="" className="h-5 w-auto" />
              }
            />
          </div>

          {socialPostPlatform && (
            <p className="mt-2 text-xs text-gray-500">
              Social post caption will be tailored to {PLATFORM_LABELS[socialPostPlatform]}
              &apos;s real WVF style (e.g. Facebook uses emoji-labeled checklists; Instagram is short
              and punchy).
            </p>
          )}

          {useKeymakersCopy && (
            <div className="mt-3 max-w-sm">
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
              <p className="mt-1 text-xs text-gray-500">
                Newsletter will adapt this real WVF recruitment message instead of standard event
                promotion. Reference copy — still needs Maria&apos;s approval before sending.
              </p>
            </div>
          )}
        </div>

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
      className={`flex flex-col items-center gap-1.5 rounded-lg border px-4 py-3 text-xs font-semibold transition disabled:cursor-not-allowed disabled:opacity-40 ${
        active
          ? "border-navy bg-navy text-white"
          : "border-gray-200 bg-white text-gray-600 hover:border-sky-blue hover:text-navy"
      }`}
    >
      <span className="flex h-6 w-6 items-center justify-center">{icon}</span>
      {label}
    </button>
  );
}

/** Renders a simple-icons brand icon (real, properly-licensed SVG path
 * data — see simple-icons npm package, CC0/MIT licensed) at a fixed size,
 * colored to match the current text color via `fill="currentColor"` so it
 * follows the toggle button's active/inactive state automatically. */
function BrandSvgIcon({ icon }: { icon: { path: string; title: string } }) {
  return (
    <svg
      viewBox="0 0 24 24"
      role="img"
      aria-label={icon.title}
      className="h-5 w-5"
      fill="currentColor"
    >
      <path d={icon.path} />
    </svg>
  );
}

/** LinkedIn has no icon in the installed simple-icons version (removed
 * from the package — see LinkedIn's own trademark enforcement history).
 * Rather than fabricate an inaccurate logo shape from memory, this is a
 * plain generic "in" monogram — not LinkedIn's real brand mark. */
function LinkedInMonogramIcon() {
  return (
    <span
      aria-label="LinkedIn"
      className="flex h-5 w-5 items-center justify-center rounded-[3px] bg-current text-[10px] font-black leading-none"
    >
      <span className="text-white mix-blend-difference">in</span>
    </span>
  );
}
