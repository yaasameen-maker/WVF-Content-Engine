const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface EventInput {
  title: string;
  date: string;
  speaker: string;
  registration_link: string;
  audience: string;
  description: string;
}

export interface SocialPostOutput {
  caption: string;
  hashtags: string[];
  suggested_image_prompt: string;
  cta: string;
}

export interface HashtagsOutput {
  primary_hashtags: string[];
  topic_hashtags: string[];
  rationale: string;
}

export interface NewsletterOutput {
  subject_line: string;
  preview_text: string;
  body: string;
  cta_text: string;
  cta_link: string;
}

export interface FlyerOutput {
  headline: string;
  subheadline: string;
  body: string;
  cta: string;
  footer_details: string;
}

export interface CalendarPostEntry {
  day_label: string;
  platform: string;
  post_idea: string;
  hashtags: string[];
  cta: string;
}

export interface ContentCalendarOutput {
  weeks: number;
  entries: CalendarPostEntry[];
}

export interface GeneratedContentResponse {
  social_post: SocialPostOutput;
  hashtags: HashtagsOutput;
  newsletter: NewsletterOutput;
  flyer: FlyerOutput;
  calendar: ContentCalendarOutput;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`API request failed (${res.status}): ${detail}`);
  }

  return res.json() as Promise<T>;
}

export function generateContent(event: EventInput): Promise<GeneratedContentResponse> {
  return request<GeneratedContentResponse>("/api/generate", {
    method: "POST",
    body: JSON.stringify(event),
  });
}
