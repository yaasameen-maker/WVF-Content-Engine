"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type { GeneratedContentResponse } from "@/lib/api";

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
      <HashtagsCard content={content} />
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

function SocialPostCard({ content }: { content: GeneratedContentResponse }) {
  const [caption, setCaption] = useState(content.social_post.caption);
  const [cta, setCta] = useState(content.social_post.cta);
  const [platformLabel, setPlatformLabel] = useState<string | null>(null);

  useEffect(() => {
    setPlatformLabel(sessionStorage.getItem("wvf_social_post_platform_label"));
  }, []);

  return (
    <Card title="Social Media Post">
      {platformLabel && (
        <div className="rounded-md border border-sky-blue bg-sky-blue/10 px-3 py-2 text-xs text-navy">
          <span className="font-bold uppercase tracking-wide">Platform template</span>
          <span className="mx-1">·</span>
          {platformLabel}
        </div>
      )}
      <LabeledTextArea label="Caption" value={caption} onChange={setCaption} rows={5} />
      <LabeledInput label="Call to Action" value={cta} onChange={setCta} />
      <div>
        <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-gray-500">
          Hashtags
        </span>
        <p className="text-sm text-sky-blue">{content.social_post.hashtags.join(" ")}</p>
      </div>
      <div>
        <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-gray-500">
          Suggested Image Prompt
        </span>
        <p className="text-sm italic text-gray-600">{content.social_post.suggested_image_prompt}</p>
      </div>
    </Card>
  );
}

function HashtagsCard({ content }: { content: GeneratedContentResponse }) {
  return (
    <Card title="Hashtag Recommendations">
      <div>
        <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-gray-500">
          Primary
        </span>
        <p className="text-sm text-sky-blue">{content.hashtags.primary_hashtags.join(" ")}</p>
      </div>
      <div>
        <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-gray-500">
          Topic-Specific
        </span>
        <p className="text-sm text-sky-blue">{content.hashtags.topic_hashtags.join(" ")}</p>
      </div>
      <p className="text-sm text-gray-600">{content.hashtags.rationale}</p>
    </Card>
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
