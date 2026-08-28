"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  disconnectFacebook,
  disconnectInstagram,
  disconnectX,
  getFacebookConnectionStatus,
  getInstagramConnectionStatus,
  getXConnectionStatus,
  getXConnectStartUrl,
  postToX,
  selectSocialVariant,
  updateContentItemBody,
  updateContentItemScheduledDate,
  type GeneratedContentResponse,
  type HashtagsOutput,
  type SocialPostVariant,
} from "@/lib/api";

export default function ReviewPage() {
  const [content, setContent] = useState<GeneratedContentResponse | null>(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    const raw = sessionStorage.getItem("wvf_generated_content");
    if (!raw) {
      setNotFound(true);
      return;
    }
    setContent(JSON.parse(raw));
  }, []);

  if (notFound) {
    return (
      <div className="text-center">
        <p className="mb-4 text-gray-600">
          No generated content found. Generate a campaign first.
        </p>
        <Link href="/" className="font-semibold text-sky-blue underline">
          Back to event form
        </Link>
      </div>
    );
  }

  if (!content) {
    return <p className="text-gray-600">Loading…</p>;
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-navy">Review Generated Content</h2>
        <p className="text-sm text-gray-600">
          Edit any field below before approving. Nothing here has been published yet.
        </p>
      </div>

      <SocialPostCard content={content} />
      <NewsletterCard content={content} />
      <FlyerCard content={content} />
      <CalendarCard content={content} />

      <Link href="/" className="inline-block text-sm font-semibold text-sky-blue underline">
        ← Generate another campaign
      </Link>
    </div>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-lg border border-gray-200 shadow-sm">
      <div className="rounded-t-lg bg-navy px-5 py-3">
        <h3 className="font-semibold text-white">{title}</h3>
      </div>
      <div className="space-y-3 px-5 py-4">{children}</div>
    </section>
  );
}

function LabeledTextArea({
  label,
  value,
  onChange,
  rows = 3,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  rows?: number;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-gray-500">
        {label}
      </span>
      <textarea
        rows={rows}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-sky-blue focus:outline-none focus:ring-2 focus:ring-sky-blue/30"
      />
    </label>
  );
}

function LabeledInput({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-gray-500">
        {label}
      </span>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-sky-blue focus:outline-none focus:ring-2 focus:ring-sky-blue/30"
      />
    </label>
  );
}

/**
 * "Post date" field — a native <input type="date">, which every modern
 * browser already renders as a small pop-up calendar on click/focus, so
 * no date-picker library is pulled in for this. Purely tags the item for
 * the /calendar view (see ContentItemResponse.scheduled_date) — never
 * queues or triggers posting, "Post to X" is still always a manual
 * click regardless of what's set here.
 */
function PostDatePicker({
  value,
  onChange,
  label = "Post date (optional — shows on the Content Calendar)",
}: {
  value: string;
  onChange: (value: string) => void;
  label?: string;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-gray-500">
        {label}
      </span>
      <input
        type="date"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-sky-blue focus:outline-none focus:ring-2 focus:ring-sky-blue/30"
      />
    </label>
  );
}

/**
 * Social post + hashtags picker → editor.
 *
 * Staff first compares SOCIAL_POST_VARIANT_COUNT options side by side
 * (each pairing a social_post_variants[i] with hashtags_variants[i] by
 * index — see GeneratedContentResponse). Picking one calls
 * selectSocialVariant() to persist that pair as the event's ContentItems
 * (social_post/hashtags don't exist in the DB before this), then the card
 * collapses into the same editable form the rest of the review page uses.
 */
function SocialPostCard({ content }: { content: GeneratedContentResponse }) {
  const [pickedIndex, setPickedIndex] = useState<number | null>(null);
  const [savedContentItemId, setSavedContentItemId] = useState<number | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [platformLabel, setPlatformLabel] = useState<string | null>(null);

  useEffect(() => {
    setPlatformLabel(sessionStorage.getItem("wvf_social_post_platform_label"));
  }, []);

  async function pick(index: number) {
    setSaveError(null);
    setIsSaving(true);
    try {
      const saved = await selectSocialVariant(
        content.event_id,
        content.social_post_variants[index],
        content.hashtags_variants[index].hashtags
      );
      const socialPostItem = saved.find((item) => item.content_type === "social_post");
      if (!socialPostItem) {
        throw new Error("Server didn't return the saved social post — try again.");
      }
      setSavedContentItemId(socialPostItem.id);
      setPickedIndex(index);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Failed to save your pick.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <Card title="Social Media Post & Hashtags">
      {platformLabel && (
        <div className="rounded-md border border-sky-blue bg-sky-blue/10 px-3 py-2 text-xs text-navy">
          <span className="font-bold uppercase tracking-wide">Platform template</span>
          <span className="mx-1">·</span>
          {platformLabel}
        </div>
      )}

      {pickedIndex === null ? (
        <div className="space-y-3">
          <p className="text-sm text-gray-600">
            Compare {content.social_post_variants.length} options and pick one to edit and use.
          </p>
          {saveError && (
            <div className="rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
              {saveError}
            </div>
          )}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            {content.social_post_variants.map((variant, i) => (
              <SocialPostVariantOption
                key={i}
                variant={variant}
                hashtags={content.hashtags_variants[i].hashtags}
                onPick={() => pick(i)}
                disabled={isSaving}
              />
            ))}
          </div>
        </div>
      ) : (
        <SocialPostEditor
          variant={content.social_post_variants[pickedIndex]}
          hashtags={content.hashtags_variants[pickedIndex].hashtags}
          contentItemId={savedContentItemId}
          onChangeOption={() => setPickedIndex(null)}
        />
      )}
    </Card>
  );
}

function SocialPostVariantOption({
  variant,
  hashtags,
  onPick,
  disabled,
}: {
  variant: SocialPostVariant;
  hashtags: HashtagsOutput;
  onPick: () => void;
  disabled: boolean;
}) {
  return (
    <div className="flex flex-col rounded-lg border border-gray-200 p-4">
      <span className="mb-2 self-start rounded-full bg-sky-blue/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-navy">
        {variant.structure_label}
      </span>
      <p className="mb-3 flex-1 whitespace-pre-wrap text-sm text-gray-800">{variant.post.caption}</p>
      <p className="mb-3 text-xs text-sky-blue">{hashtags.primary_hashtags.join(" ")}</p>
      <button
        type="button"
        onClick={onPick}
        disabled={disabled}
        className="rounded-md bg-navy px-3 py-2 text-sm font-semibold text-white transition hover:bg-navy/90 disabled:cursor-not-allowed disabled:opacity-50"
      >
        Use this one
      </button>
    </div>
  );
}

function SocialPostEditor({
  variant,
  hashtags,
  contentItemId,
  onChangeOption,
}: {
  variant: SocialPostVariant;
  hashtags: HashtagsOutput;
  contentItemId: number | null;
  onChangeOption: () => void;
}) {
  const [caption, setCaption] = useState(variant.post.caption);
  const [cta, setCta] = useState(variant.post.cta);
  const [scheduledDate, setScheduledDate] = useState("");
  const [dateSaveError, setDateSaveError] = useState<string | null>(null);

  async function handleDateChange(next: string) {
    setScheduledDate(next);
    setDateSaveError(null);
    if (contentItemId === null) return;
    try {
      await updateContentItemScheduledDate(contentItemId, next || null);
    } catch (err) {
      setDateSaveError(err instanceof Error ? err.message : "Failed to save post date.");
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="rounded-full bg-sky-blue/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-navy">
          {variant.structure_label}
        </span>
        <button type="button" onClick={onChangeOption} className="text-xs font-semibold text-sky-blue hover:underline">
          ← Compare options again
        </button>
      </div>
      <PostDatePicker value={scheduledDate} onChange={handleDateChange} />
      {dateSaveError && <p className="text-xs text-red-600">{dateSaveError}</p>}
      <LabeledTextArea label="Caption" value={caption} onChange={setCaption} rows={5} />
      <LabeledInput label="Call to Action" value={cta} onChange={setCta} />
      <div>
        <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-gray-500">
          Primary Hashtags
        </span>
        <p className="text-sm text-sky-blue">{hashtags.primary_hashtags.join(" ")}</p>
      </div>
      <div>
        <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-gray-500">
          Topic-Specific Hashtags
        </span>
        <p className="text-sm text-sky-blue">{hashtags.topic_hashtags.join(" ")}</p>
      </div>
      <p className="text-xs text-gray-500">{hashtags.rationale}</p>
      <div>
        <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-gray-500">
          Suggested Image Prompt
        </span>
        <p className="text-sm italic text-gray-600">{variant.post.suggested_image_prompt}</p>
      </div>

      {contentItemId !== null && (
        <PostToXButton
          contentItemId={contentItemId}
          currentBody={{
            caption,
            cta,
            hashtags: [...hashtags.primary_hashtags, ...hashtags.topic_hashtags],
            suggested_image_prompt: variant.post.suggested_image_prompt,
          }}
        />
      )}
      <div className="flex flex-wrap gap-2">
        <MetaConnectButton platform="instagram" />
        <MetaConnectButton platform="facebook" />
      </div>
    </div>
  );
}

/**
 * Manual-click "Post to X" — connects the account if needed, saves
 * whatever caption is currently on screen (so a staff edit isn't
 * silently dropped), then publishes it. Never fires on its own; only in
 * direct response to a click. See docs/STATUS_AND_SCOPE.md's Aug 8
 * manual-click scope decision.
 */
function PostToXButton({
  contentItemId,
  currentBody,
}: {
  contentItemId: number;
  currentBody: Record<string, unknown>;
}) {
  const [connected, setConnected] = useState<boolean | null>(null);
  const [xUsername, setXUsername] = useState<string | null>(null);
  const [isPosting, setIsPosting] = useState(false);
  const [postError, setPostError] = useState<string | null>(null);
  const [postedId, setPostedId] = useState<string | null>(null);

  useEffect(() => {
    getXConnectionStatus()
      .then((status) => {
        setConnected(status.connected);
        setXUsername(status.username);
      })
      .catch(() => setConnected(false));
  }, []);

  function connectX() {
    window.location.href = getXConnectStartUrl();
  }

  async function handleDisconnect() {
    await disconnectX();
    setConnected(false);
    setXUsername(null);
  }

  async function handlePostToX() {
    setPostError(null);
    setIsPosting(true);
    try {
      // Save the currently-edited caption/CTA before posting, so "Post
      // to X" publishes what's actually on screen, not the original
      // AI-generated text if it's since been edited.
      await updateContentItemBody(contentItemId, currentBody);
      const result = await postToX(contentItemId);
      setPostedId(result.external_post_id);
    } catch (err) {
      setPostError(err instanceof Error ? err.message : "Failed to post to X.");
    } finally {
      setIsPosting(false);
    }
  }

  if (connected === null) {
    return null; // still loading connection status
  }

  return (
    <div className="rounded-md border border-gray-200 bg-gray-50/50 px-4 py-3">
      {!connected && (
        <button
          type="button"
          onClick={connectX}
          className="rounded-md bg-black px-4 py-2 text-sm font-semibold text-white transition hover:bg-gray-800"
        >
          Connect X to enable posting
        </button>
      )}

      {connected && postedId && (
        <p className="text-sm font-semibold text-green-700">
          Posted to X (@{xUsername}) — post ID {postedId}.
        </p>
      )}

      {connected && !postedId && (
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={handlePostToX}
            disabled={isPosting}
            className="rounded-md bg-black px-4 py-2 text-sm font-semibold text-white transition hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isPosting ? "Posting…" : `Post to X (@${xUsername})`}
          </button>
          <button
            type="button"
            onClick={handleDisconnect}
            className="text-xs font-semibold text-gray-500 hover:underline"
          >
            Disconnect X
          </button>
        </div>
      )}

      {postError && (
        <div className="mt-2 rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
          {postError}
        </div>
      )}
    </div>
  );
}

const META_PLATFORM_LABELS = { instagram: "Instagram", facebook: "Facebook" } as const;

/**
 * Connect-only button for Instagram/Facebook — both go through Meta's
 * Graph API (see backend app/services/meta_client.py). Unlike
 * PostToXButton, this doesn't offer an actual "Post to..." action yet:
 * publishing requires `pages_manage_posts`/`instagram_content_publish`,
 * which stay locked behind Meta App Review until WVF's Meta Developer
 * app is approved — that's a manual review on Meta's side, not something
 * this app can complete on its own. Connecting the account (Facebook
 * Login + picking up the linked Page/IG account) works today regardless.
 */
function MetaConnectButton({ platform }: { platform: "instagram" | "facebook" }) {
  const [connected, setConnected] = useState<boolean | null>(null);
  const [username, setUsername] = useState<string | null>(null);

  const getStatus = platform === "instagram" ? getInstagramConnectionStatus : getFacebookConnectionStatus;
  const disconnect = platform === "instagram" ? disconnectInstagram : disconnectFacebook;

  useEffect(() => {
    getStatus()
      .then((status) => {
        setConnected(status.connected);
        setUsername(status.username);
      })
      .catch(() => setConnected(false));
    // getStatus/disconnect are stable per platform prop, not per render —
    // re-running this on every render would just re-fetch identical status.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [platform]);

  async function handleDisconnect() {
    await disconnect();
    setConnected(false);
    setUsername(null);
  }

  if (connected === null) {
    return null; // still loading connection status
  }

  const label = META_PLATFORM_LABELS[platform];

  if (!connected) {
    return (
      <button
        type="button"
        disabled
        title="Instagram/Facebook connect is built but not usable yet — WVF's Meta Developer app still needs to be registered and pass Meta's App Review."
        className="cursor-not-allowed rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-semibold text-gray-400"
      >
        Connect {label} (Coming soon)
      </button>
    );
  }

  return (
    <div className="flex items-center gap-3 rounded-md border border-gray-200 bg-gray-50/50 px-4 py-2">
      <span className="text-sm font-semibold text-gray-700">
        {label} connected ({username}) — publishing pending Meta App Review
      </span>
      <button type="button" onClick={handleDisconnect} className="text-xs font-semibold text-gray-500 hover:underline">
        Disconnect
      </button>
    </div>
  );
}

function NewsletterCard({ content }: { content: GeneratedContentResponse }) {
  const [subject, setSubject] = useState(content.newsletter.subject_line);
  const [preview, setPreview] = useState(content.newsletter.preview_text);
  const [body, setBody] = useState(content.newsletter.body);
  const [bodyPlainText, setBodyPlainText] = useState(content.newsletter.body_plain_text);
  const [ctaText, setCtaText] = useState(content.newsletter.cta_text);
  const [keymakersStageLabel, setKeymakersStageLabel] = useState<string | null>(null);

  useEffect(() => {
    setKeymakersStageLabel(sessionStorage.getItem("wvf_keymakers_stage_label"));
  }, []);

  return (
    <Card title="Newsletter">
      {keymakersStageLabel && (
        <div className="rounded-md border border-sky-blue bg-sky-blue/10 px-3 py-2 text-xs text-navy">
          <span className="font-bold uppercase tracking-wide">Keymakers recruitment copy</span>
          <span className="mx-1">·</span>
          {keymakersStageLabel}
          <span className="block text-[11px] font-normal text-gray-600">
            Still needs Maria&apos;s approval before sending.
          </span>
        </div>
      )}
      <LabeledInput label="Subject Line" value={subject} onChange={setSubject} />
      <LabeledInput label="Preview Text" value={preview} onChange={setPreview} />
      <div>
        <div className="mb-1 flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">
            Body (HTML)
          </span>
          <CopyButton value={body} />
        </div>
        <textarea
          rows={6}
          value={body}
          onChange={(e) => setBody(e.target.value)}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-sky-blue focus:outline-none focus:ring-2 focus:ring-sky-blue/30"
        />
      </div>
      <div>
        <div className="mb-1 flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">
            Body (Plain Text) — for ESP export
          </span>
          <CopyButton value={bodyPlainText} />
        </div>
        <textarea
          rows={6}
          value={bodyPlainText}
          onChange={(e) => setBodyPlainText(e.target.value)}
          className="w-full rounded-md border border-gray-300 px-3 py-2 font-mono text-sm focus:border-sky-blue focus:outline-none focus:ring-2 focus:ring-sky-blue/30"
        />
      </div>
      <LabeledInput label="CTA Text" value={ctaText} onChange={setCtaText} />
    </Card>
  );
}

function CopyButton({ value }: { value: string }) {
  const [copied, setCopied] = useState(false);

  return (
    <button
      type="button"
      onClick={() => {
        navigator.clipboard.writeText(value);
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      }}
      className="text-xs font-semibold text-sky-blue hover:underline"
    >
      {copied ? "Copied!" : "Copy"}
    </button>
  );
}

function FlyerCard({ content }: { content: GeneratedContentResponse }) {
  const [headline, setHeadline] = useState(content.flyer.headline);
  const [subheadline, setSubheadline] = useState(content.flyer.subheadline);
  const [body, setBody] = useState(content.flyer.body);
  const [cta, setCta] = useState(content.flyer.cta);

  return (
    <Card title="Flyer Copy">
      <LabeledInput label="Headline" value={headline} onChange={setHeadline} />
      <LabeledInput label="Subheadline" value={subheadline} onChange={setSubheadline} />
      <LabeledTextArea label="Body" value={body} onChange={setBody} rows={4} />
      <LabeledInput label="Call to Action" value={cta} onChange={setCta} />
      <p className="text-xs text-gray-500">{content.flyer.footer_details}</p>
    </Card>
  );
}

function CalendarCard({ content }: { content: GeneratedContentResponse }) {
  return (
    <Card title={`Content Calendar (${content.calendar.weeks} weeks)`}>
      <ul className="divide-y divide-gray-100">
        {content.calendar.entries.map((entry, i) => (
          <li key={i} className="py-3 first:pt-0 last:pb-0">
            <p className="text-sm font-semibold text-navy">
              {entry.day_label} · {entry.platform}
            </p>
            <p className="text-sm text-gray-700">{entry.post_idea}</p>
            <p className="text-sm text-sky-blue">{entry.hashtags.join(" ")}</p>
            <p className="text-xs text-gray-500">CTA: {entry.cta}</p>
          </li>
        ))}
      </ul>
    </Card>
  );
}
