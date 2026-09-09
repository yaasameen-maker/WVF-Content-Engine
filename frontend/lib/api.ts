const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface EventInput {
  title: string;
  date: string;
  speaker: string;
  // Optional (Aug 2026): staff can generate content before a link exists
  // and add it later by editing the generated copy — see prompts.py's
  // _registration_line() for how the backend omits any registration
  // CTA/link when this is unset, rather than generating a broken one.
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

/** One social post option within a 3-variant generation batch (see
 * GeneratedContentResponse.social_post_variants). structure_variant is
 * the raw key ("standard"/"listicle"/"quote_style", or a platform key) —
 * pass it back as-is when persisting via selectSocialVariant(). */
export interface SocialPostVariant {
  structure_variant: string;
  structure_label: string;
  post: SocialPostOutput;
}

export interface HashtagsOutput {
  primary_hashtags: string[];
  topic_hashtags: string[];
  rationale: string;
}

/** One hashtag-set option, paired 1:1 by array index with the
 * SocialPostVariant generated alongside it — see
 * GeneratedContentResponse.hashtags_variants. */
export interface HashtagsVariant {
  hashtags: HashtagsOutput;
}

export interface NewsletterOutput {
  subject_line: string;
  preview_text: string;
  body: string;
  body_plain_text: string;
  cta_text: string;
  // null when the event had no registration link at generation time —
  // staff can add the real link later by editing the generated copy.
  cta_link: string | null;
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
  /** Pass back to selectSocialVariant() once staff picks a social post
   * option — social_post/hashtags aren't persisted until that call. */
  event_id: number;
  /** Parallel arrays — same length, same index = generated together. */
  social_post_variants: SocialPostVariant[];
  hashtags_variants: HashtagsVariant[];
  newsletter: NewsletterOutput;
  flyer: FlyerOutput;
  calendar: ContentCalendarOutput;
}

export interface ContentItemResponse {
  id: number;
  event_id: number | null;
  key_maker_id: number | null;
  content_type: string;
  block_type: string | null;
  platform: string | null;
  status: string;
  structure_variant: string | null;
  body: Record<string, unknown>;
  /** Staff-set target publish date shown on /calendar, ISO "YYYY-MM-DD".
   * Null falls back to the parent event's own date there. Purely
   * organizational — never queues or triggers posting. */
  scheduled_date: string | null;
  /** Optional free-text time-of-day reminder (e.g. "2:30 PM") — display
   * only, not combined into a real datetime and not read by any
   * automation. Posting stays a manual "Post to X" click regardless. */
  scheduled_time: string | null;
  /** Name of the approver who approved this item (see backend
   * app/models/approver.py) — null until a passcode-gated approve
   * actually happens. Never the passcode itself. */
  approved_by_name: string | null;
  /** True once this item's scheduled_date/time is more than 72 hours in
   * the past and it was never actually published — the scheduler stops
   * auto-posting it at that point (see backend app/services/scheduling.py),
   * but status is left alone so a human can still manually "Post to X". */
  is_stale: boolean;
  created_at: string;
  updated_at: string;
}

export interface EventWithContentResponse {
  id: number;
  title: string;
  date: string;
  speaker: string;
  registration_link: string;
  audience: string;
  description: string;
  created_at: string;
  updated_at: string;
  content_items: ContentItemResponse[];
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

/** Platform-specific social post structure variants (see
 * SOCIAL_POST_PLATFORM_VARIANTS in prompts.py) — a deliberate staff
 * choice, distinct from tone-variant rotation (standard/listicle/
 * quote_style), which stays random ("generate_new") unless a platform is
 * explicitly picked here. instagram/linkedin/facebook are grounded in
 * real WVF post screenshots; x/tiktok use generic platform conventions
 * only — no real WVF X/TikTok samples have been reviewed yet. */
export const SOCIAL_POST_PLATFORMS = ["instagram", "linkedin", "facebook", "x", "tiktok"] as const;
export type SocialPostPlatform = (typeof SOCIAL_POST_PLATFORMS)[number];

export interface GenerateOptions {
  /** When set, the newsletter is generated by adapting the selected real
   * Keymakers recruitment reference message instead of normal event
   * promotion — see GET /api/keymakers-stages for valid keys. */
  keymakersStageKey?: string;
  /** When set, the social post is generated for this specific platform's
   * real observed structure (see SOCIAL_POST_PLATFORMS) instead of the
   * default random tone-variant rotation. */
  socialPostPlatform?: SocialPostPlatform;
  /** Optional recurring-series steering (e.g. "Financial Literacy
   * Friday") — see GET /api/social-post-series for valid keys. Silently
   * ignored server-side if unrecognized. */
  socialPostSeries?: string;
  /** Optional tone steering (e.g. "urgent") — see GET /api/social-post-tones
   * for valid keys. Silently ignored server-side if unrecognized. */
  socialPostTone?: string;
}

export function generateContent(
  event: EventInput,
  options?: GenerateOptions
): Promise<GeneratedContentResponse> {
  return request<GeneratedContentResponse>("/api/generate", {
    method: "POST",
    body: JSON.stringify({
      ...event,
      ...(options?.keymakersStageKey
        ? { keymakers_stage_key: options.keymakersStageKey }
        : {}),
      ...(options?.socialPostPlatform
        ? { social_post_platform: options.socialPostPlatform }
        : {}),
      ...(options?.socialPostSeries ? { social_post_series: options.socialPostSeries } : {}),
      ...(options?.socialPostTone ? { social_post_tone: options.socialPostTone } : {}),
    }),
  });
}

export function listSocialPostSeries(): Promise<Record<string, string>> {
  return request<Record<string, string>>("/api/social-post-series");
}

export function listSocialPostTones(): Promise<Record<string, string>> {
  return request<Record<string, string>>("/api/social-post-tones");
}

/** Persists the social post + hashtags option staff picked from the
 * 3-variant batch generateContent() returned. Must be called exactly
 * once per event, after generateContent() — social_post/hashtags
 * ContentItems don't exist in the database until this runs. Returns the
 * two newly-created ContentItemResponse rows (social post, then
 * hashtags). */
export function selectSocialVariant(
  eventId: number,
  socialPostVariant: SocialPostVariant,
  hashtags: HashtagsOutput
): Promise<ContentItemResponse[]> {
  return request<ContentItemResponse[]>("/api/content/select-social-variant", {
    method: "POST",
    body: JSON.stringify({
      event_id: eventId,
      social_post_variant: socialPostVariant,
      hashtags,
    }),
  });
}

export function listEvents(): Promise<EventWithContentResponse[]> {
  return request<EventWithContentResponse[]>("/api/events");
}

export function listKeymakersStages(): Promise<Record<string, string>> {
  return request<Record<string, string>>("/api/keymakers-stages");
}

/** One Keymakers stage's full real reference copy (label, audience,
 * subject line options, body) — the actual WVF campaign message text,
 * for instant display without an AI generation call. */
export interface KeymakersStageDetail {
  label: string;
  audience: string;
  stage: string;
  send_day: number;
  subject_options: string[] | null;
  body: string;
}

export function getKeymakersStageDetail(stageKey: string): Promise<KeymakersStageDetail> {
  return request<KeymakersStageDetail>(`/api/keymakers-stages/${encodeURIComponent(stageKey)}`);
}

export function listInstagramTemplates(): Promise<Record<string, string>> {
  return request<Record<string, string>>("/api/instagram-templates");
}

/** One real, published WVF Instagram post's full caption and hashtags —
 * for instant display/editing without an AI generation call.
 * truncated=true means the source screenshot cut off part of the real
 * caption — show a warning, don't present it as complete. */
export interface InstagramTemplateDetail {
  label: string;
  category: string;
  caption: string;
  hashtags: string[];
  truncated: boolean;
}

export function getInstagramTemplateDetail(templateKey: string): Promise<InstagramTemplateDetail> {
  return request<InstagramTemplateDetail>(`/api/instagram-templates/${encodeURIComponent(templateKey)}`);
}

export function listXTemplates(): Promise<Record<string, string>> {
  return request<Record<string, string>>("/api/x-templates");
}

/** One real, published WVF X post's full caption and hashtags — for
 * instant display/editing without an AI generation call. See
 * InstagramTemplateDetail.truncated for what truncated=true means. */
export interface XTemplateDetail {
  label: string;
  category: string;
  caption: string;
  hashtags: string[];
  truncated: boolean;
}

export function getXTemplateDetail(templateKey: string): Promise<XTemplateDetail> {
  return request<XTemplateDetail>(`/api/x-templates/${encodeURIComponent(templateKey)}`);
}

/** Whether WVF's X account is connected, and its username if so — never
 * exposes tokens. See POST /api/oauth/x/start for the connect flow
 * (a full-page redirect, not fetched via this client). */
export interface XConnectionStatus {
  connected: boolean;
  username: string | null;
}

export function getXConnectionStatus(): Promise<XConnectionStatus> {
  return request<XConnectionStatus>("/api/social/x/status");
}

/** Starts the X OAuth connect flow — a real navigation, not a fetch,
 * since it needs to leave the app and go to X's authorization screen.
 * Call this from a click handler via `window.location.href =
 * getXConnectStartUrl()`. */
export function getXConnectStartUrl(): string {
  return `${API_URL}/api/oauth/x/start`;
}

export async function disconnectX(): Promise<void> {
  await request<{ disconnected: boolean }>("/api/social/x/connection", { method: "DELETE" });
}

/** Instagram + Facebook both connect through one Meta Graph API OAuth
 * dialog (see backend app/services/meta_client.py) — connecting works
 * today, but publishing 403s until WVF's Meta Developer app passes App
 * Review. The "Connect" buttons exist so the login step can be tested/
 * used independently of that approval, which is out of this app's
 * control and can take days to weeks once submitted. */
export interface MetaConnectionStatus {
  connected: boolean;
  username: string | null;
}

export function getInstagramConnectionStatus(): Promise<MetaConnectionStatus> {
  return request<MetaConnectionStatus>("/api/social/instagram/status");
}

export function getFacebookConnectionStatus(): Promise<MetaConnectionStatus> {
  return request<MetaConnectionStatus>("/api/social/facebook/status");
}

/** Both Instagram and Facebook use the same Meta OAuth start route —
 * which one gets connected depends on what the user's Facebook Page has
 * linked, not which button was clicked (see meta_oauth_callback). */
export function getMetaConnectStartUrl(): string {
  return `${API_URL}/api/oauth/meta/start`;
}

export async function disconnectInstagram(): Promise<void> {
  await request<{ disconnected: boolean }>("/api/social/instagram/connection", { method: "DELETE" });
}

export async function disconnectFacebook(): Promise<void> {
  await request<{ disconnected: boolean }>("/api/social/facebook/connection", { method: "DELETE" });
}

/** Saves staff edits to a content item's body before it's posted/used
 * elsewhere — e.g. the edited caption in the review page's social post
 * editor, so "Post to X" publishes what's actually on screen rather
 * than the original AI-generated/template text. */
export function updateContentItemBody(
  contentItemId: number,
  body: Record<string, unknown>
): Promise<ContentItemResponse> {
  return request<ContentItemResponse>(`/api/content/${contentItemId}`, {
    method: "PATCH",
    body: JSON.stringify({ body }),
  });
}

/** Moves a content item from draft to approved — passcode-gated (see
 * backend app/models/approver.py): Nancy and Maria each have their own
 * name + passcode, so approval records who actually signed off, which
 * matters now that approval is the hard gate before scheduled
 * auto-posting to X. Doesn't post/send anything by itself; "Post to X"
 * is still a separate manual click. Throws (via request()'s non-ok
 * handling) with a 401 message on wrong name/passcode. */
export function approveContentItem(
  contentItemId: number,
  approverName: string,
  passcode: string
): Promise<ContentItemResponse> {
  return request<ContentItemResponse>(`/api/content/${contentItemId}/approve`, {
    method: "POST",
    body: JSON.stringify({ approver_name: approverName, passcode }),
  });
}

/** Requests a passcode reset link be emailed to the approver, if that
 * name matches a real approver with an email on file — always resolves
 * the same way regardless, so this can't be used to enumerate valid
 * approver names (see backend POST /api/approvers/forgot-passcode). */
export async function requestPasscodeReset(approverName: string): Promise<void> {
  await request<{ ok: boolean }>("/api/approvers/forgot-passcode", {
    method: "POST",
    body: JSON.stringify({ approver_name: approverName }),
  });
}

/** Consumes a reset link's token (from the emailed URL's ?approver=
 * &token= query params) to set a new passcode. Throws with a 400 message
 * if the link is invalid/expired/already used. */
export async function resetPasscode(
  approverId: number,
  token: string,
  newPasscode: string
): Promise<void> {
  await request<{ ok: boolean }>("/api/approvers/reset-passcode", {
    method: "POST",
    body: JSON.stringify({ approver_id: approverId, token, new_passcode: newPasscode }),
  });
}

/** Sets/clears a content item's target publish date and/or an optional
 * free-text time-of-day reminder, shown on /calendar. Purely an
 * organizational tag/note (see backend ContentItem.scheduled_date/
 * scheduled_time's model comments) — never queues or triggers posting;
 * "Post to X" is still always a manual click regardless of these values.
 * Pass null to clear a field. */
export function updateContentItemScheduledDate(
  contentItemId: number,
  scheduledDate: string | null,
  scheduledTime?: string | null
): Promise<ContentItemResponse> {
  return request<ContentItemResponse>(`/api/content/${contentItemId}`, {
    method: "PATCH",
    body: JSON.stringify({
      scheduled_date: scheduledDate,
      ...(scheduledTime !== undefined ? { scheduled_time: scheduledTime } : {}),
    }),
  });
}

/** Persists a fixed-template post (real WVF Instagram/X copy, not
 * AI-generated) as a scheduled content item — templates have no source
 * event, so unlike selectSocialVariant() this doesn't take an event_id.
 * See backend POST /api/content/schedule-template. */
export function scheduleTemplate(params: {
  platform: string;
  caption: string;
  hashtags: string[];
  scheduledDate: string;
  scheduledTime?: string;
}): Promise<ContentItemResponse> {
  return request<ContentItemResponse>("/api/content/schedule-template", {
    method: "POST",
    body: JSON.stringify({
      platform: params.platform,
      caption: params.caption,
      hashtags: params.hashtags,
      scheduled_date: params.scheduledDate,
      scheduled_time: params.scheduledTime || null,
    }),
  });
}

/** Content items with a scheduled_date but no parent event (e.g. saved
 * via scheduleTemplate()) — GET /api/events only returns event-scoped
 * items nested under their event, so /calendar fetches this separately
 * and merges the two. */
export function listScheduledUnscopedContent(): Promise<ContentItemResponse[]> {
  return request<ContentItemResponse[]>("/api/content/scheduled");
}

export interface PostToXResponse {
  external_post_id: string;
  status: string;
}

/** Publishes an existing social_post ContentItem to X. Manual-click
 * only — call this ONLY in direct response to a staff member clicking
 * "Post to X"; never automatically. */
export function postToX(contentItemId: number): Promise<PostToXResponse> {
  return request<PostToXResponse>("/api/social/x/post", {
    method: "POST",
    body: JSON.stringify({ content_item_id: contentItemId }),
  });
}

/** A single Key Maker's PUBLIC profile fields only — never phone/email/
 * address, which have no API exposure by design (see backend
 * KeyMaker/KeyMakerPrivate).
 *
 * title/location/industry/key_quotes/story are only populated for 4 of
 * the 10 real Key Makers as of Aug 2026 (see seed_key_makers_public.py)
 * — the other 6 have these as null, same "bio pending" treatment as
 * testimonial_quote. Never render null as blank or fabricated text. */
export interface KeyMakerResponse {
  id: number;
  business_name: string;
  owner_name: string;
  business_type: string | null;
  website: string | null;
  social_media: string | null;
  testimonial_quote: string | null;
  video_link: string | null;
  photo_url: string | null;
  title: string | null;
  location: string | null;
  industry: string | null;
  key_quotes: string[] | null;
  story: string | null;
}

export function listKeyMakers(): Promise<KeyMakerResponse[]> {
  return request<KeyMakerResponse[]>("/api/key-makers");
}

export function getKeyMaker(keyMakerId: number): Promise<KeyMakerResponse> {
  return request<KeyMakerResponse>(`/api/key-makers/${keyMakerId}`);
}

/** A staff-uploaded photo (event photos, Key Maker headshots, etc.) —
 * see backend app/models/media.py. Proposed scope addition, not yet
 * approved by WVF. */
export interface PhotoAssetResponse {
  id: number;
  object_key: string;
  public_url: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  key_maker_id: number | null;
  event_id: number | null;
  caption: string | null;
  uploaded_by: string | null;
  created_at: string;
}

interface PresignUploadResponse {
  upload_url: string;
  object_key: string;
}

/** Step 1 of 3 for uploading a photo: ask the backend for a URL to
 * upload straight to R2. The backend never receives the file bytes —
 * see confirmPhotoUpload() for step 3 and object_storage.py for why. */
function presignPhotoUpload(filename: string, contentType: string): Promise<PresignUploadResponse> {
  return request<PresignUploadResponse>("/api/media/presign-upload", {
    method: "POST",
    body: JSON.stringify({ filename, content_type: contentType }),
  });
}

/** Step 3 of 3: tell the backend the direct-to-R2 upload (step 2)
 * succeeded, so it can persist the photo's metadata row. */
function confirmPhotoUpload(params: {
  objectKey: string;
  filename: string;
  contentType: string;
  sizeBytes: number;
  keyMakerId?: number;
  eventId?: number;
  caption?: string;
  uploadedBy?: string;
}): Promise<PhotoAssetResponse> {
  return request<PhotoAssetResponse>("/api/media/photos", {
    method: "POST",
    body: JSON.stringify({
      object_key: params.objectKey,
      filename: params.filename,
      content_type: params.contentType,
      size_bytes: params.sizeBytes,
      key_maker_id: params.keyMakerId ?? null,
      event_id: params.eventId ?? null,
      caption: params.caption ?? null,
      uploaded_by: params.uploadedBy ?? null,
    }),
  });
}

/** Full upload flow: presign -> direct browser PUT to R2 -> confirm.
 * Callers just need a File object; this handles all three steps. */
export async function uploadPhoto(
  file: File,
  metadata?: { keyMakerId?: number; eventId?: number; caption?: string; uploadedBy?: string }
): Promise<PhotoAssetResponse> {
  const { upload_url, object_key } = await presignPhotoUpload(file.name, file.type);

  const uploadRes = await fetch(upload_url, {
    method: "PUT",
    headers: { "Content-Type": file.type },
    body: file,
  });
  if (!uploadRes.ok) {
    throw new Error(`Upload to storage failed (${uploadRes.status})`);
  }

  return confirmPhotoUpload({
    objectKey: object_key,
    filename: file.name,
    contentType: file.type,
    sizeBytes: file.size,
    ...metadata,
  });
}

export function listPhotos(params?: { keyMakerId?: number; eventId?: number }): Promise<PhotoAssetResponse[]> {
  const query = new URLSearchParams();
  if (params?.keyMakerId != null) query.set("key_maker_id", String(params.keyMakerId));
  if (params?.eventId != null) query.set("event_id", String(params.eventId));
  const qs = query.toString();
  return request<PhotoAssetResponse[]>(`/api/media/photos${qs ? `?${qs}` : ""}`);
}

export function deletePhoto(photoId: number): Promise<{ ok: boolean }> {
  return request<{ ok: boolean }>(`/api/media/photos/${photoId}`, { method: "DELETE" });
}
