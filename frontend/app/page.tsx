"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { siFacebook, siInstagram, siTiktok, siX } from "simple-icons";
import { SideRailPortal } from "@/components/SideRailSlot";
import {
  generateContent,
  getInstagramTemplateDetail,
  getKeymakersStageDetail,
  getXTemplateDetail,
  listInstagramTemplates,
  listKeymakersStages,
  listSocialPostSeries,
  listSocialPostTones,
  listXTemplates,
  scheduleTemplate,
  SOCIAL_POST_PLATFORMS,
  type EventInput,
  type InstagramTemplateDetail,
  type KeymakersStageDetail,
  type SocialPostPlatform,
  type XTemplateDetail,
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
 * instantly, no AI call. instagram/linkedin/facebook/x/tiktok reveal a
 * sub-choice (AI Copy — tailored to that platform's style where real
 * samples exist — or Fixed template). "ai" reveals the event-form →
 * Generate Campaign flow directly, platform-agnostic — used by the Email
 * Copy section's "AI Generate" button (Keymakers-flavored generation is
 * driven by keymakersStageKey, not by a platform selection). */
type Mode = SocialPostPlatform | "keymakers" | "ai" | null;

/** Once a platform tile is selected, which of the two sub-options (if
 * any) is active. Reset whenever the platform tile changes. */
type PlatformSubMode = "ai" | "fixed" | null;

/** Whether the Social Media Copy section's standalone "AI Generate" form
 * is open. Fully independent of the platform tiles below it (`mode` /
 * `platformSubMode`) — opening this never touches tile state, and opening
 * a tile never touches this. Two separate entry points into AI
 * generation, each with its own state, so neither can reset the other. */
type SocialAiPickerState = "closed" | "open";

export default function EventFormPage() {
  const router = useRouter();
  const [event, setEvent] = useState<EventInput>(EMPTY_EVENT);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [mode, setMode] = useState<Mode>(null);
  const [platformSubMode, setPlatformSubMode] = useState<PlatformSubMode>(null);

  // Social Media Copy section's own standalone "AI Generate" flow — a
  // second, fully independent entry point into generation, separate from
  // the platform tiles above (mode/platformSubMode/event). Its
  // own event fields, own platform choice, own generating/error state, so
  // using one flow can never reset or collide with the other.
  const [socialAiPicker, setSocialAiPicker] = useState<SocialAiPickerState>("closed");
  const [socialAiPlatform, setSocialAiPlatform] = useState<SocialPostPlatform>("instagram");
  const [socialAiEvent, setSocialAiEvent] = useState<EventInput>(EMPTY_EVENT);
  const [socialAiGenerating, setSocialAiGenerating] = useState(false);
  const [socialAiError, setSocialAiError] = useState<string | null>(null);
  // Optional steering, both default to "" (unset) — server silently
  // ignores an empty/unrecognized value, same as leaving it out entirely.
  const [socialPostSeriesOptions, setSocialPostSeriesOptions] = useState<Record<string, string> | null>(
    null
  );
  const [socialPostTonesOptions, setSocialPostTonesOptions] = useState<Record<string, string> | null>(
    null
  );
  const [socialAiSeries, setSocialAiSeries] = useState("");
  const [socialAiTone, setSocialAiTone] = useState("");

  const [keymakersStages, setKeymakersStages] = useState<Record<string, string> | null>(null);
  const [keymakersStageKey, setKeymakersStageKey] = useState("");
  const [keymakersDetail, setKeymakersDetail] = useState<KeymakersStageDetail | null>(null);
  const [keymakersDetailError, setKeymakersDetailError] = useState<string | null>(null);

  const [instagramTemplates, setInstagramTemplates] = useState<Record<string, string> | null>(null);
  const [instagramTemplateKey, setInstagramTemplateKey] = useState("");
  const [instagramTemplateDetail, setInstagramTemplateDetail] = useState<InstagramTemplateDetail | null>(
    null
  );
  const [instagramTemplateError, setInstagramTemplateError] = useState<string | null>(null);

  const [xTemplates, setXTemplates] = useState<Record<string, string> | null>(null);
  const [xTemplateKey, setXTemplateKey] = useState("");
  const [xTemplateDetail, setXTemplateDetail] = useState<XTemplateDetail | null>(null);
  const [xTemplateError, setXTemplateError] = useState<string | null>(null);

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

  useEffect(() => {
    listInstagramTemplates()
      .then((templates) => {
        setInstagramTemplates(templates);
        const firstKey = Object.keys(templates)[0];
        if (firstKey) setInstagramTemplateKey(firstKey);
      })
      .catch(() => {
        // Non-fatal: Fixed template just won't be usable if this fails —
        // AI Copy still works independently.
        setInstagramTemplates({});
      });
  }, []);

  useEffect(() => {
    listSocialPostSeries()
      .then(setSocialPostSeriesOptions)
      .catch(() => {
        // Non-fatal: the series dropdown just won't have options — the
        // form still works with series left unset.
        setSocialPostSeriesOptions({});
      });
    listSocialPostTones()
      .then(setSocialPostTonesOptions)
      .catch(() => {
        setSocialPostTonesOptions({});
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

  // Fetch the real Instagram post template whenever "Fixed template" is
  // selected for the Instagram tile and a template is chosen — instant
  // reference content, not an AI generation call.
  useEffect(() => {
    if (mode !== "instagram" || platformSubMode !== "fixed" || !instagramTemplateKey) return;
    setInstagramTemplateError(null);
    getInstagramTemplateDetail(instagramTemplateKey)
      .then(setInstagramTemplateDetail)
      .catch((err) =>
        setInstagramTemplateError(err instanceof Error ? err.message : "Failed to load this template.")
      );
  }, [mode, platformSubMode, instagramTemplateKey]);

  useEffect(() => {
    listXTemplates()
      .then((templates) => {
        setXTemplates(templates);
        const firstKey = Object.keys(templates)[0];
        if (firstKey) setXTemplateKey(firstKey);
      })
      .catch(() => {
        setXTemplates({});
      });
  }, []);

  // Fetch the real X post template whenever "Fixed template" is selected
  // for the X tile and a template is chosen — instant reference content,
  // not an AI generation call.
  useEffect(() => {
    if (mode !== "x" || platformSubMode !== "fixed" || !xTemplateKey) return;
    setXTemplateError(null);
    getXTemplateDetail(xTemplateKey)
      .then(setXTemplateDetail)
      .catch((err) =>
        setXTemplateError(err instanceof Error ? err.message : "Failed to load this template.")
      );
  }, [mode, platformSubMode, xTemplateKey]);

  function updateField(field: keyof EventInput, value: string) {
    setEvent((prev) => ({ ...prev, [field]: value }));
  }

  function selectMode(next: Mode) {
    // Closes the standalone Social AI Generate picker whenever a platform
    // tile is picked — both share the same collapsed rail/panel space, so
    // leaving the AI Generate panel open while a platform panel also tries
    // to open pinned the AI Generate panel on screen and made every other
    // tile look unresponsive (they were still "active" underneath it).
    setSocialAiPicker("closed");
    setMode((prev) => (prev === next ? null : next));
    setPlatformSubMode(null);
  }

  /** Social Media Copy section's own standalone "AI Generate" button. Its
   * platform is chosen via a dropdown inside its own form, not by picking a
   * tile — but it shares the same rail/panel space as the platform tiles,
   * so opening it closes whichever platform tile is active (see selectMode
   * for the reverse direction). */
  function openSocialAiForm() {
    setSocialAiError(null);
    setMode(null);
    setPlatformSubMode(null);
    setSocialAiPicker((prev) => (prev === "open" ? "closed" : "open"));
  }

  /** Email Copy section's "AI Generate" — jumps straight to the generic
   * AI flow (mode "ai"), same as the standalone AI Copy tile used to.
   * No picker needed: Keymakers-flavored generation is driven by the
   * keymakersStageKey dropdown below, not a platform selection. */
  function startEmailAiGenerate() {
    selectMode("ai");
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

  function updateSocialAiField(field: keyof EventInput, value: string) {
    setSocialAiEvent((prev) => ({ ...prev, [field]: value }));
  }

  /** Submit handler for the Social Media Copy section's own standalone AI
   * Generate form — entirely separate from handleSubmit()/event above.
   * Uses its own event fields and its own platform dropdown selection. */
  async function handleSocialAiSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSocialAiError(null);
    setSocialAiGenerating(true);

    try {
      const result = await generateContent(socialAiEvent, {
        socialPostPlatform: socialAiPlatform,
        socialPostSeries: socialAiSeries || undefined,
        socialPostTone: socialAiTone || undefined,
      });
      sessionStorage.setItem("wvf_generated_content", JSON.stringify(result));
      sessionStorage.setItem("wvf_source_event", JSON.stringify(socialAiEvent));
      sessionStorage.removeItem("wvf_keymakers_stage_label");
      sessionStorage.setItem("wvf_social_post_platform_label", PLATFORM_LABELS[socialAiPlatform]);
      router.push("/review");
    } catch (err) {
      setSocialAiError(err instanceof Error ? err.message : "Something went wrong generating content.");
    } finally {
      setSocialAiGenerating(false);
    }
  }

  const keymakersDisabled = !keymakersStages || Object.keys(keymakersStages).length === 0;

  return (
    <div>
      <InstagramGradientDef />


      {/* Both sections share one rail/panel: any tile from either section
          expanding collapses every other tile from BOTH sections into the
          same rail, docked to the window's true left edge via
          SideRailPortal (not just left of the panel within this centered
          column) — and its panel appears in the normal centered flow. */}
      {(() => {
        const anyExpanded = mode !== null || socialAiPicker === "open";
        const socialTiles = (
          <TileRail expanded={anyExpanded}>
            <PlatformToggleButton
              tileId="instagram"
              label="Instagram"
              active={mode === "instagram"}
              collapsed={anyExpanded}
              onClick={() => selectMode("instagram")}
              icon={<BrandSvgIcon icon={siInstagram} fill={`url(#${IG_GRADIENT_ID})`} />}
            />
            <PlatformToggleButton
              tileId="linkedin"
              label="LinkedIn"
              active={mode === "linkedin"}
              collapsed={anyExpanded}
              onClick={() => selectMode("linkedin")}
              icon={<LinkedInMonogramIcon />}
            />
            <PlatformToggleButton
              tileId="facebook"
              label="Facebook"
              active={mode === "facebook"}
              collapsed={anyExpanded}
              onClick={() => selectMode("facebook")}
              icon={<BrandSvgIcon icon={siFacebook} fill={`#${siFacebook.hex}`} />}
            />
            <PlatformToggleButton
              tileId="x"
              label="X"
              active={mode === "x"}
              collapsed={anyExpanded}
              onClick={() => selectMode("x")}
              icon={<BrandSvgIcon icon={siX} fill={`#${siX.hex}`} />}
            />
            <PlatformToggleButton
              tileId="tiktok"
              label="TikTok"
              active={mode === "tiktok"}
              collapsed={anyExpanded}
              onClick={() => selectMode("tiktok")}
              icon={<TikTokIcon />}
            />
            <PlatformToggleButton
              tileId="social-ai-generate"
              label="AI Generate"
              active={socialAiPicker === "open"}
              collapsed={anyExpanded}
              onClick={openSocialAiForm}
              icon={<AiSparkleIcon />}
            />
          </TileRail>
        );
        const emailTiles = (
          <TileRail expanded={anyExpanded}>
            <PlatformToggleButton
              tileId="keymakers"
              label="Keymakers Copy"
              active={mode === "keymakers"}
              collapsed={anyExpanded}
              onClick={() => selectMode("keymakers")}
              disabled={keymakersDisabled}
              icon={
                // h-full w-full + object-contain (not a fixed h-16): this
                // icon renders inside two very differently sized wrappers
                // (a 64px full-tile slot and a 32px collapsed-rail slot)
                // — a fixed height overflowed the small slot instead of
                // scaling down into it.
                // eslint-disable-next-line @next/next/no-img-element
                <img src="/wvf-logo.svg" alt="" className="h-full w-full object-contain" />
              }
            />
            <PlatformToggleButton
              tileId="email-ai-generate"
              label="AI Generate"
              active={mode === "ai"}
              collapsed={anyExpanded}
              onClick={startEmailAiGenerate}
              icon={<AiSparkleIcon />}
            />
          </TileRail>
        );

        // Grid mode: each section's real heading sits directly above ITS
        // OWN tile group (not both headings stacked together at the top,
        // far from one of the two groups). Once a tile is expanded, only
        // the active section's heading remains. Rail mode: both groups
        // portal to the shared left-edge slot, each still under its own
        // small label — expanding either section still collapses both
        // (one shared expand state), only the grouping/labeling is
        // section-scoped.
        return (
          <div className="mb-8">
            {anyExpanded ? (
              <SideRailPortal>
                <div className="flex flex-col gap-8">
                  <div>
                    <p className="m-0 px-1 text-[10px] font-bold uppercase leading-tight tracking-wide text-gray-400">
                      Social
                    </p>
                    {socialTiles}
                  </div>
                  <div>
                    <p className="m-0 px-1 text-[10px] font-bold uppercase leading-tight tracking-wide text-gray-400">
                      Email
                    </p>
                    {emailTiles}
                  </div>
                </div>
              </SideRailPortal>
            ) : (
              <>
                <div className="mb-3">
                  <h2 className="text-lg font-bold text-navy">Social Media Copy</h2>
                  <p className="text-sm text-gray-600">
                    Pick a platform, then choose a real WVF template — or use the AI Generate tile
                    for a new AI-written post.
                  </p>
                </div>
                {socialTiles}

                <div className="mb-3 mt-8">
                  <h2 className="text-lg font-bold text-navy">Email Copy</h2>
                  <p className="text-sm text-gray-600">
                    Real WVF Keymakers recruitment copy, or use the AI Generate tile for a new
                    AI-written newsletter.
                  </p>
                </div>
                {emailTiles}
              </>
            )}

            <AnimatePresence>
              {socialAiPicker === "open" && (
                  <TileExpandedPanel
                    title="AI Generate — Social Post"
                    onClose={() => setSocialAiPicker("closed")}
                  >
                    <Field label="Platform">
                      <select
                        value={socialAiPlatform}
                        onChange={(e) => setSocialAiPlatform(e.target.value as SocialPostPlatform)}
                        className="input"
                      >
                        {SOCIAL_POST_PLATFORMS.map((platform) => (
                          <option key={platform} value={platform}>
                            {PLATFORM_LABELS[platform]}
                          </option>
                        ))}
                      </select>
                    </Field>

                    <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
                      <Field label="Series (optional)">
                        <select
                          value={socialAiSeries}
                          onChange={(e) => setSocialAiSeries(e.target.value)}
                          className="input"
                        >
                          <option value="">Not part of a series</option>
                          {Object.entries(socialPostSeriesOptions ?? {}).map(([key, label]) => (
                            <option key={key} value={key}>
                              {label}
                            </option>
                          ))}
                        </select>
                      </Field>

                      <Field label="Tone (optional)">
                        <select
                          value={socialAiTone}
                          onChange={(e) => setSocialAiTone(e.target.value)}
                          className="input"
                        >
                          <option value="">Default</option>
                          {Object.entries(socialPostTonesOptions ?? {}).map(([key, label]) => (
                            <option key={key} value={key}>
                              {label}
                            </option>
                          ))}
                        </select>
                      </Field>
                    </div>

                    <form onSubmit={handleSocialAiSubmit} className="mt-4 space-y-4">
                      <Field label="Event Title">
                        <input
                          required
                          type="text"
                          value={socialAiEvent.title}
                          onChange={(e) => updateSocialAiField("title", e.target.value)}
                          className="input"
                          placeholder="Money & Credit: Understanding Your Credit Report"
                        />
                      </Field>

                      <Field label="Date">
                        <EventDateTimePicker
                          value={socialAiEvent.date}
                          onChange={(next) => updateSocialAiField("date", next)}
                        />
                      </Field>

                      <Field label="Speaker">
                        <input
                          required
                          type="text"
                          value={socialAiEvent.speaker}
                          onChange={(e) => updateSocialAiField("speaker", e.target.value)}
                          className="input"
                          placeholder="WVF Financial Education Team"
                        />
                      </Field>

                      <Field label="Registration Link (optional — add later if not ready)">
                        <input
                          type="url"
                          value={socialAiEvent.registration_link}
                          onChange={(e) => updateSocialAiField("registration_link", e.target.value)}
                          className="input"
                          placeholder="https://www.womenventurefund.org/events/..."
                        />
                      </Field>

                      <Field label="Target Audience">
                        <input
                          required
                          type="text"
                          value={socialAiEvent.audience}
                          onChange={(e) => updateSocialAiField("audience", e.target.value)}
                          className="input"
                          placeholder="NYC-based women entrepreneurs, Spanish-speaking community welcome"
                        />
                      </Field>

                      <Field label="Description">
                        <textarea
                          required
                          rows={4}
                          value={socialAiEvent.description}
                          onChange={(e) => updateSocialAiField("description", e.target.value)}
                          className="input"
                          placeholder="Describe the event, what attendees will learn, and any relevant details..."
                        />
                      </Field>

                      {socialAiError && (
                        <div className="rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
                          {socialAiError}
                        </div>
                      )}

                      <button
                        type="submit"
                        disabled={socialAiGenerating}
                        className="rounded-md bg-navy px-6 py-3 font-semibold text-white transition hover:bg-navy/90 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {socialAiGenerating ? "Generating…" : "Generate Campaign"}
                      </button>
                    </form>
                  </TileExpandedPanel>
                )}

                {activePlatform && (
                  <TileExpandedPanel
                    title={`${PLATFORM_LABELS[activePlatform]}: how do you want to start?`}
                    onClose={() => selectMode(activePlatform)}
                  >
                    <div className="flex flex-wrap gap-2">
                      <button
                        type="button"
                        onClick={() => setPlatformSubMode("ai")}
                        className={`rounded-md border-2 px-4 py-2 text-sm font-semibold transition ${
                          platformSubMode === "ai"
                            ? "border-navy bg-navy text-white"
                            : "border-gray-200 bg-white text-gray-600 hover:border-sky-blue hover:text-navy"
                        }`}
                      >
                        AI Copy + AI Hashtags
                      </button>
                      <button
                        type="button"
                        onClick={() => setPlatformSubMode("fixed")}
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
                      <div className="mt-3 space-y-4">
                        <div className="space-y-2">
                          <p className="text-xs text-gray-500">
                            <span className="font-semibold text-navy">AI Copy:</span>{" "}
                            {REAL_SAMPLE_GROUNDED_PLATFORMS.includes(activePlatform)
                              ? `a new caption tailored to ${PLATFORM_LABELS[activePlatform]}'s real WVF style (grounded in real WVF posts).`
                              : `a new caption following general ${PLATFORM_LABELS[activePlatform]} conventions — not yet grounded in real WVF ${PLATFORM_LABELS[activePlatform]} posts, since none have been reviewed for this platform.`}
                          </p>
                          <p className="text-xs text-gray-500">
                            <span className="font-semibold text-navy">AI Hashtags:</span> a matching
                            hashtag set, generated alongside the caption — you&apos;ll get 3 caption +
                            hashtag pairs to compare on the review page.
                          </p>
                        </div>

                        <form onSubmit={handleSubmit} className="space-y-4">
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
                            <EventDateTimePicker value={event.date} onChange={(next) => updateField("date", next)} />
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

                          <Field label="Registration Link (optional — add later if not ready)">
                            <input
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
                              rows={4}
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
                      </div>
                    )}

                    {platformSubMode === "fixed" && activePlatform === "instagram" && (
                      <div className="mt-3">
                        {instagramTemplateError && (
                          <div className="mb-3 rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
                            {instagramTemplateError}
                          </div>
                        )}
                        <span className="mb-1 block text-sm font-medium text-navy">
                          Which real Instagram post?
                        </span>
                        <select
                          value={instagramTemplateKey}
                          onChange={(e) => setInstagramTemplateKey(e.target.value)}
                          className="input"
                        >
                          {Object.entries(instagramTemplates ?? {}).map(([key, label]) => (
                            <option key={key} value={key}>
                              {label}
                            </option>
                          ))}
                        </select>

                        {instagramTemplateDetail && !instagramTemplateError && (
                          <div className="mt-3 rounded-lg border border-gray-200 shadow-sm">
                            <div className="rounded-t-lg bg-navy px-5 py-3">
                              <h3 className="font-semibold text-white">
                                {instagramTemplateDetail.label}
                              </h3>
                            </div>
                            <div className="space-y-3 px-5 py-4">
                              <pre className="whitespace-pre-wrap font-sans text-sm text-gray-800">
                                {instagramTemplateDetail.caption}
                              </pre>
                              {instagramTemplateDetail.hashtags.length > 0 && (
                                <p className="text-sm text-sky-blue">
                                  {instagramTemplateDetail.hashtags.join(" ")}
                                </p>
                              )}
                              {instagramTemplateDetail.truncated && (
                                <p className="text-xs font-semibold text-red-600">
                                  ⚠ This post was cut off in the source screenshot — double-check the
                                  full caption before reusing.
                                </p>
                              )}
                              <p className="text-xs font-semibold text-amber-700">
                                Real, previously-published WVF Instagram post — edit as needed before
                                reuse.
                              </p>
                              <ScheduleTemplateButton
                                platform="instagram"
                                caption={instagramTemplateDetail.caption}
                                hashtags={instagramTemplateDetail.hashtags}
                              />
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {platformSubMode === "fixed" && activePlatform === "x" && (
                      <div className="mt-3">
                        {xTemplateError && (
                          <div className="mb-3 rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
                            {xTemplateError}
                          </div>
                        )}
                        <span className="mb-1 block text-sm font-medium text-navy">
                          Which real X post?
                        </span>
                        <select
                          value={xTemplateKey}
                          onChange={(e) => setXTemplateKey(e.target.value)}
                          className="input"
                        >
                          {Object.entries(xTemplates ?? {}).map(([key, label]) => (
                            <option key={key} value={key}>
                              {label}
                            </option>
                          ))}
                        </select>

                        {xTemplateDetail && !xTemplateError && (
                          <div className="mt-3 rounded-lg border border-gray-200 shadow-sm">
                            <div className="rounded-t-lg bg-navy px-5 py-3">
                              <h3 className="font-semibold text-white">{xTemplateDetail.label}</h3>
                            </div>
                            <div className="space-y-3 px-5 py-4">
                              <pre className="whitespace-pre-wrap font-sans text-sm text-gray-800">
                                {xTemplateDetail.caption}
                              </pre>
                              {xTemplateDetail.hashtags.length > 0 && (
                                <p className="text-sm text-sky-blue">
                                  {xTemplateDetail.hashtags.join(" ")}
                                </p>
                              )}
                              {xTemplateDetail.truncated && (
                                <p className="text-xs font-semibold text-red-600">
                                  ⚠ This post was cut off in the source screenshot (e.g. a shortened
                                  link) — double-check the full caption before reusing.
                                </p>
                              )}
                              <p className="text-xs font-semibold text-amber-700">
                                Real, previously-published WVF X post — edit as needed before reuse.
                              </p>
                              <ScheduleTemplateButton
                                platform="x"
                                caption={xTemplateDetail.caption}
                                hashtags={xTemplateDetail.hashtags}
                              />
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {platformSubMode === "fixed" &&
                      activePlatform !== "instagram" &&
                      activePlatform !== "x" && (
                        <div className="mt-3 rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                          A fixed (non-AI) {PLATFORM_LABELS[activePlatform]} template isn&apos;t
                          available yet — real sample WVF {PLATFORM_LABELS[activePlatform]} posts are
                          needed to build one, so this doesn&apos;t show fabricated content in
                          WVF&apos;s name. Use AI Copy in the meantime.
                        </div>
                      )}
                  </TileExpandedPanel>
                )}

                {mode === "keymakers" && (
                  <TileExpandedPanel
                    title="Keymakers Copy"
                    onClose={() => selectMode("keymakers")}
                  >
                    <span className="mb-1 block text-sm font-medium text-navy">
                      Which Keymakers message?
                    </span>
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
                            {keymakersDetail.subject_options &&
                              keymakersDetail.subject_options.length > 0 && (
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
                  </TileExpandedPanel>
                )}

                {mode === "ai" && (
                  <TileExpandedPanel
                    title="AI Generate — Newsletter"
                    onClose={() => selectMode("ai")}
                  >
                    <form onSubmit={handleSubmit} className="space-y-4">
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
                        <EventDateTimePicker value={event.date} onChange={(next) => updateField("date", next)} />
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

                      <Field label="Registration Link (optional — add later if not ready)">
                        <input
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
                          rows={4}
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
                  </TileExpandedPanel>
                )}
              </AnimatePresence>
            </div>
          );
        })()}

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

// Matches "August 15, 2026 at 2:00 PM ET" — the free-text format this
// field has always stored (see EventInput.date in lib/api.ts: plain
// string, interpolated as-is into every prompt in prompts.py, never
// parsed). Used to pre-fill the picker's date/time inputs when editing
// an existing value written in this exact shape; anything else (a
// value typed before this picker existed, or hand-edited) just leaves
// the picker blank rather than guessing a bad partial parse.
const EVENT_DATE_STRING_RE =
  /^([A-Za-z]+ \d{1,2}, \d{4})(?: at (\d{1,2}):(\d{2}) (AM|PM))? ET$/;

function formatEventDateTime(dateStr: string, timeStr: string): string {
  if (!dateStr) return "";
  // dateStr is "YYYY-MM-DD" from <input type="date">, parsed as local
  // (not UTC) by splitting manually — `new Date("YYYY-MM-DD")` parses as
  // UTC midnight and can roll back a day once formatted in a local zone
  // behind UTC.
  const [y, m, d] = dateStr.split("-").map(Number);
  const dateLabel = new Date(y, m - 1, d).toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });
  if (!timeStr) return dateLabel;
  const [hh, mm] = timeStr.split(":").map(Number);
  const period = hh >= 12 ? "PM" : "AM";
  const hour12 = hh % 12 === 0 ? 12 : hh % 12;
  return `${dateLabel} at ${hour12}:${String(mm).padStart(2, "0")} ${period} ET`;
}

/**
 * Event date + time picker — two native inputs (<input type="date"> and
 * <input type="time">), each of which browsers already render as a
 * pop-up picker on click/focus, composed into the same free-text
 * "August 15, 2026 at 2:00 PM ET" string this field has always stored
 * (see EventInput.date — interpolated as-is into every generation
 * prompt, never parsed as a real Date). Replaces free-typing that string
 * by hand.
 */
function EventDateTimePicker({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  const match = value.match(EVENT_DATE_STRING_RE);
  const [datePart, setDatePart] = useState("");
  const [timePart, setTimePart] = useState("");

  useEffect(() => {
    if (!match) return;
    const parsedDate = new Date(match[1]);
    if (Number.isNaN(parsedDate.getTime())) return;
    const y = parsedDate.getFullYear();
    const m = String(parsedDate.getMonth() + 1).padStart(2, "0");
    const d = String(parsedDate.getDate()).padStart(2, "0");
    setDatePart(`${y}-${m}-${d}`);
    if (match[2]) {
      let hh = Number(match[2]) % 12;
      if (match[4] === "PM") hh += 12;
      setTimePart(`${String(hh).padStart(2, "0")}:${match[3]}`);
    }
    // Only re-derive when the incoming value changes shape (e.g. loading a
    // different draft) — not on every keystroke, since this effect's own
    // onChange calls would otherwise fight the user's in-progress edits.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  function handleDateChange(next: string) {
    setDatePart(next);
    onChange(formatEventDateTime(next, timePart));
  }

  function handleTimeChange(next: string) {
    setTimePart(next);
    onChange(formatEventDateTime(datePart, next));
  }

  return (
    <div className="flex gap-3">
      <input
        required
        type="date"
        value={datePart}
        onChange={(e) => handleDateChange(e.target.value)}
        className="input"
      />
      <input
        type="time"
        value={timePart}
        onChange={(e) => handleTimeChange(e.target.value)}
        className="input"
      />
    </div>
  );
}

/**
 * "Schedule this post" for a real fixed-template post — date picker
 * (native <input type="date">, which browsers already render as a
 * pop-up calendar) plus a save button. Templates are display-only until
 * this is clicked; saving persists it as a real content_items row via
 * POST /api/content/schedule-template so it shows up on /calendar.
 * Purely organizational — does not post anything (see
 * ContentItemResponse.scheduled_date's comment in lib/api.ts).
 */
function ScheduleTemplateButton({
  platform,
  caption,
  hashtags,
}: {
  platform: string;
  caption: string;
  hashtags: string[];
}) {
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedId, setSavedId] = useState<number | null>(null);

  async function handleSchedule() {
    if (!date) {
      setError("Pick a date first.");
      return;
    }
    setError(null);
    setIsSaving(true);
    try {
      const saved = await scheduleTemplate({
        platform,
        caption,
        hashtags,
        scheduledDate: date,
        scheduledTime: time || undefined,
      });
      setSavedId(saved.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to schedule this post.");
    } finally {
      setIsSaving(false);
    }
  }

  if (savedId !== null) {
    return (
      <p className="mt-3 text-sm font-semibold text-green-700">
        Scheduled for {date}
        {time ? ` at ${time}` : ""} — it now shows on the{" "}
        <a href="/calendar" className="underline">
          Content Calendar
        </a>
        .
      </p>
    );
  }

  return (
    <div className="mt-3 flex flex-wrap items-end gap-3">
      <div className="w-48">
        <Field label="Post date">
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="input"
          />
        </Field>
      </div>
      <div className="w-40">
        <Field label="Time (optional)">
          <input
            type="time"
            value={time}
            onChange={(e) => setTime(e.target.value)}
            className="input"
          />
        </Field>
      </div>
      <button
        type="button"
        onClick={handleSchedule}
        disabled={isSaving}
        className="rounded-md bg-navy px-4 py-2 text-sm font-semibold text-white transition hover:bg-navy/90 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isSaving ? "Scheduling…" : "Schedule this post"}
      </button>
      {error && <p className="w-full text-xs text-red-600">{error}</p>}
    </div>
  );
}

/** A tile in a FLIP-animated tile row (see TileRail). `tileId` must be
 * unique within the row and is what Framer Motion uses (via layoutId) to
 * morph this exact tile into its matching TileExpandedPanel when
 * selected — the two must share the same `tile-${tileId}` id. `collapsed`
 * renders a compact icon-only square (for the rail state); otherwise the
 * full card with label. */
function PlatformToggleButton({
  tileId,
  label,
  icon,
  active,
  collapsed = false,
  disabled,
  onClick,
}: {
  tileId: string;
  label: string;
  icon: React.ReactNode;
  active: boolean;
  collapsed?: boolean;
  disabled?: boolean;
  onClick: () => void;
}) {
  if (collapsed) {
    return (
      <motion.button
        type="button"
        layoutId={`tile-${tileId}`}
        onClick={onClick}
        disabled={disabled}
        title={label}
        transition={TILE_SPRING}
        className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-lg border-2 bg-white transition disabled:cursor-not-allowed disabled:opacity-40 ${
          active ? "border-navy" : "border-gray-200 hover:border-sky-blue"
        }`}
      >
        <span className="flex h-8 w-8 items-center justify-center">{icon}</span>
      </motion.button>
    );
  }

  return (
    <motion.button
      type="button"
      layoutId={`tile-${tileId}`}
      onClick={onClick}
      disabled={disabled}
      aria-pressed={active}
      transition={TILE_SPRING}
      className={`flex flex-col items-center gap-3 rounded-xl border-2 px-10 py-7 text-lg font-semibold transition disabled:cursor-not-allowed disabled:opacity-40 ${
        active
          ? "border-navy bg-navy text-white"
          : "border-gray-200 bg-white text-gray-600 hover:border-sky-blue hover:text-navy"
      }`}
    >
      <span className="flex h-16 w-16 items-center justify-center">{icon}</span>
      {label}
    </motion.button>
  );
}

const TILE_SPRING = { type: "spring", stiffness: 300, damping: 30 } as const;

/** Wraps a row of tiles: renders as a wrapping grid when nothing is
 * selected, or a compact vertical rail (tiles collapse to icon-only
 * squares) once `expanded` is true — the FLIP/shared-layout transition
 * between the two states is automatic via each tile's shared layoutId
 * with its TileExpandedPanel. Mirrors the Profiles page's Key Maker
 * rail pattern. Driven entirely by `expanded`, not a viewport breakpoint
 * — the app's content column is capped at max-w-4xl (896px), narrower
 * than Tailwind's lg: breakpoint (1024px), so lg:-gated rail classes
 * silently never applied on any normal window size and the rail/panel
 * rendered stacked instead of side by side. */
function TileRail({ expanded, children }: { expanded: boolean; children: React.ReactNode }) {
  return (
    <motion.div
      layout
      transition={TILE_SPRING}
      className={
        expanded
          ? "flex w-20 shrink-0 flex-col gap-2"
          : "flex flex-wrap gap-4"
      }
    >
      {children}
    </motion.div>
  );
}

/** The panel shown for the currently-active tile. Its matching rail icon
 * (see PlatformToggleButton) stays visible in the rail too — highlighted
 * with a navy ring — rather than morphing into this panel and
 * disappearing from the rail, so nothing the user just clicked seems to
 * vanish. Because both the rail icon and this panel are on-screen at
 * once, they can't share one Framer Motion layoutId (only one mounted
 * instance of a given layoutId animates correctly) — this uses a plain
 * fade/slide-in instead of a shared-layout morph. `onClose` collapses
 * back to the tile grid. */
function TileExpandedPanel({
  title,
  onClose,
  children,
}: {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 8 }}
      transition={TILE_SPRING}
      className="flex-1 overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm"
    >
      <div className="flex items-center justify-between gap-4 bg-navy px-6 py-4">
        <h3 className="text-lg font-bold text-white">{title}</h3>
        <button
          type="button"
          onClick={onClose}
          aria-label="Back to all options"
          className="shrink-0 rounded-full px-3 py-1 text-sm font-semibold text-white/80 hover:bg-white/10 hover:text-white"
        >
          ← Back
        </button>
      </div>
      <div className="max-w-2xl p-6">{children}</div>
    </motion.div>
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
  // h-full w-full (not a fixed h-16): this icon renders inside two very
  // differently sized wrappers (a 64px full-tile slot and a 32px
  // collapsed-rail slot) — a fixed pixel size overflowed the small slot
  // instead of scaling down into it, same issue the Keymakers <img> had.
  return (
    <svg viewBox="0 0 24 24" role="img" aria-label={icon.title} className="h-full w-full" fill={fill}>
      <path d={icon.path} />
    </svg>
  );
}

/** TikTok's real mark is three offset-colored layers (cyan behind-left,
 * red/pink behind-right, black on top) — simple-icons only ships a flat
 * single-color brand path, same limitation Instagram's gradient works
 * around (see InstagramGradientDef). Renders the same note-shape path
 * three times with real TikTok brand colors and small pixel offsets to
 * reproduce that layered look, rather than the flat black glyph. */
function TikTokIcon() {
  // viewBox is wider than the path's own 24x24 box (with the group
  // shifted +1,+1 to re-center it) so the offset cyan/red copies have
  // room to render fully instead of being clipped at the SVG bounds —
  // the plain siTiktok path fills close to the full 24x24 already, so
  // any translate() with no extra margin pushed part of the shape
  // outside the viewBox and got cut off.
  return (
    <svg viewBox="0 0 26 26" role="img" aria-label="TikTok" className="h-full w-full">
      <g transform="translate(1, 1)">
        <path d={siTiktok.path} fill="#25F4EE" transform="translate(-0.6, -0.6)" />
        <path d={siTiktok.path} fill="#FE2C55" transform="translate(0.6, 0.6)" />
        <path d={siTiktok.path} fill="#000000" />
      </g>
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
 * Hand-drawn to match LinkedIn's real mark (dot-over-"i", bold "n", white
 * glyph on brand blue #0A66C2 rounded-square badge) rather than a plain
 * text monogram — see the reference image this was built from (Aug 2026). */
function LinkedInMonogramIcon() {
  // Badge is a drawn <rect> filling the full 0-24 viewBox, not a CSS
  // background-color on the <svg> — that previous approach rendered
  // visibly smaller/inset than the other brand tiles' full-bleed icons.
  // Glyph path is the standard open-source LinkedIn "in" mark (the same
  // widely-published outline used by Font Awesome's brand set), not a
  // hand-tuned approximation — earlier hand-drawn passes kept reading as
  // too thin/small next to the reference image.
  return (
    <svg viewBox="0 0 24 24" role="img" aria-label="LinkedIn" className="h-full w-full">
      <rect x="0" y="0" width="24" height="24" rx="4.5" fill="#0A66C2" />
      <path
        fill="#FFFFFF"
        transform="translate(3, 3) scale(0.04018)"
        d="M100.28 448H7.4V148.9h92.88zM53.79 108.1C24.09 108.1 0 83.5 0 53.8a53.79 53.79 0 0 1 107.58 0c0 29.7-24.1 54.3-53.79 54.3zM447.9 448h-92.68V302.4c0-34.7-.7-79.2-48.29-79.2-48.29 0-55.69 37.7-55.69 76.7V448h-92.78V148.9h89.08v40.8h1.3c12.4-23.5 42.69-48.3 87.88-48.3 94 0 111.28 61.9 111.28 142.3V448z"
      />
    </svg>
  );
}

/** Simple sparkle glyph marking the AI-generation tile — not a brand mark,
 * just a plain hand-drawn shape in the WVF sky-blue so it doesn't compete
 * visually with the real brand icons beside it. `fill` defaults to the
 * sky-blue brand color but accepts an override (e.g. white) for when the
 * tile itself is in its active/selected navy-background state, matching
 * how the X/TikTok tile icons swap fill on active. */
function AiSparkleIcon({
  className = "h-full w-full",
  fill = "#6FA8DC",
}: {
  className?: string;
  fill?: string;
}) {
  return (
    <svg viewBox="0 0 24 24" role="img" aria-label="AI Generate" className={className} fill={fill}>
      <path d="M12 2l1.8 5.2L19 9l-5.2 1.8L12 16l-1.8-5.2L5 9l5.2-1.8L12 2z" />
      <path d="M19 14l.9 2.6L22.5 17.5l-2.6.9L19 21l-.9-2.6-2.6-.9 2.6-.9L19 14z" />
    </svg>
  );
}
