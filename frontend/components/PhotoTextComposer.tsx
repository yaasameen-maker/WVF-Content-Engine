"use client";

import { useEffect, useRef, useState } from "react";
import {
  listKeyMakers,
  listPhotos,
  searchStockPhotos,
  uploadComposedImage,
  type ComposedImageResponse,
  type KeyMakerResponse,
  type PhotoAssetResponse,
  type StockPhotoResult,
} from "@/lib/api";

/**
 * Photo + text overlay composer — proposed scope addition, not yet
 * approved by WVF (see backend app/models/media.py's ComposedImage
 * docstring). Staff pick a blank Layout (a vector-drawn frame of color
 * blocks + a reserved photo region — see LAYOUTS below), pick a photo
 * from the library to drop into that region, then drag a text layer
 * over the result (pre-filled with the generated headline/caption).
 * Flattens to a PNG entirely in the browser via <canvas> — this
 * component never sends image bytes to the backend until the final
 * flattened PNG is ready to upload.
 *
 * The Layouts are original vector frames modeled on the STRUCTURE of
 * real WVF flyer styles (see docs/x-post-audit-2026-09.md's "Recurring
 * flyer template patterns observed" — photo-top/color-block-bottom,
 * diagonal-split-with-circular-photo, full-bleed-with-dark-band), not
 * a text-removed copy of any specific designed graphic — this tool has
 * no image-editing capability to alter an existing photo/flyer file.
 *
 * Only mounts once a real ContentItem exists (contentItemId is required,
 * not optional) — a composite always attaches to an already-saved
 * content item, never an in-progress draft, matching how
 * ComposedImageCreate.content_item_id is required server-side too.
 */

const CANVAS_WIDTH = 1080;
const CANVAS_HEIGHT = 1080;

/** On-screen preview size in CSS pixels — set as an explicit inline
 * style (not a Tailwind responsive class) so the canvas element's
 * rendered box is unambiguous rather than depending on how w-full/
 * aspect-square resolve inside this component's particular parent
 * layout. Bigger than the canvas's own former max-w-sm (384px) cap so
 * staff can actually see the full post while editing, not just a
 * thumbnail. */
const PREVIEW_DISPLAY_SIZE = 560;

const NAVY = "#4A7EBB";
const SKY_BLUE = "#87ACD1";

interface TextLayer {
  text: string;
  xPct: number; // center x, 0-1 fraction of canvas width
  yPct: number; // center y, 0-1 fraction of canvas height
  fontSizePx: number;
  color: string;
}

const DEFAULT_LAYER: Omit<TextLayer, "text"> = {
  xPct: 0.5,
  yPct: 0.82,
  fontSizePx: 64,
  color: "#FFFFFF",
};

/** Where the photo gets drawn within the canvas, as a fraction box
 * (x, y, w, h all 0-1) — lets a layout reserve part of the frame for
 * solid color blocks instead of a full-bleed photo. */
interface PhotoRegion {
  x: number;
  y: number;
  w: number;
  h: number;
}

/** A blank starting frame — color blocks, a photo region, and a default
 * text position — drawn entirely as vector shapes (no source image),
 * approximating the structure of a real WVF flyer style without
 * reproducing any specific designed graphic. Staff pick one, then drop
 * in their own photo and text. See docs/x-post-audit-2026-09.md's
 * "Recurring flyer template patterns observed" for what these are
 * modeled after. */
interface Layout {
  key: string;
  label: string;
  photoRegion: PhotoRegion | null; // null = no photo area, solid color frame only
  defaultLayer: Omit<TextLayer, "text">;
  /** Draws this layout's color blocks/frame — called before the photo
   * and text so blocks sit behind both. */
  drawFrame: (ctx: CanvasRenderingContext2D) => void;
}

const LAYOUTS: Layout[] = [
  {
    key: "workshop",
    label: "Workshop — photo top, color block bottom",
    photoRegion: { x: 0, y: 0, w: 1, h: 0.55 },
    defaultLayer: { xPct: 0.5, yPct: 0.72, fontSizePx: 70, color: "#FFFFFF" },
    drawFrame(ctx) {
      ctx.fillStyle = "#FFFFFF";
      ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
      ctx.fillStyle = NAVY;
      ctx.fillRect(0, CANVAS_HEIGHT * 0.55, CANVAS_WIDTH, CANVAS_HEIGHT * 0.45);
    },
  },
  {
    key: "conference",
    label: "Conference — diagonal split, circular photo",
    photoRegion: { x: 0.32, y: 0.16, w: 0.5, h: 0.5 },
    defaultLayer: { xPct: 0.32, yPct: 0.78, fontSizePx: 56, color: "#0F1F33" },
    drawFrame(ctx) {
      ctx.fillStyle = "#FFFFFF";
      ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
      ctx.fillStyle = SKY_BLUE;
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.lineTo(CANVAS_WIDTH, 0);
      ctx.lineTo(CANVAS_WIDTH, CANVAS_HEIGHT * 0.35);
      ctx.lineTo(0, CANVAS_HEIGHT * 0.6);
      ctx.closePath();
      ctx.fill();
    },
  },
  {
    key: "gala",
    label: "Gala — full-bleed photo, dark bottom band",
    photoRegion: { x: 0, y: 0, w: 1, h: 1 },
    defaultLayer: { xPct: 0.5, yPct: 0.88, fontSizePx: 60, color: "#F4D98A" },
    drawFrame(ctx) {
      ctx.fillStyle = "#14243F";
      ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
    },
  },
  {
    key: "plain",
    label: "Plain — full-bleed photo, no frame",
    photoRegion: { x: 0, y: 0, w: 1, h: 1 },
    defaultLayer: { ...DEFAULT_LAYER },
    drawFrame(ctx) {
      ctx.fillStyle = NAVY;
      ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
    },
  },
];

/** A pickable backdrop image, normalized across the composer's three
 * sources — the staff photo library, free Pexels stock search, and
 * real Key Maker headshots (see PhotoSourceTabs below). Only
 * source: "library" carries a photoAssetId, since that's the only kind
 * ComposedImage.source_photo_id (a FK to photo_assets) can reference —
 * stock photos and Key Maker headshots aren't PhotoAsset rows. */
type SelectedImage =
  | { source: "library"; url: string; photoAssetId: number }
  | { source: "stock"; url: string }
  | { source: "keymaker"; url: string };

export function PhotoTextComposer({
  contentItemId,
  initialText,
  onSaved,
}: {
  contentItemId: number;
  initialText: string;
  /** Called with the saved ComposedImageResponse right after a
   * successful save — lets the parent (e.g. SocialPostEditor) know a
   * composite now exists for this content item, so it can stop showing
   * a "no image confirmed yet" warning next to Schedule/Approve. Not
   * called on failure, and not required — the composite stays optional
   * (see this component's own docstring), so parents that don't care
   * can simply omit it. */
  onSaved?: (result: ComposedImageResponse) => void;
}) {
  const [photos, setPhotos] = useState<PhotoAssetResponse[] | null>(null);
  const [photosError, setPhotosError] = useState<string | null>(null);
  const [keyMakers, setKeyMakers] = useState<KeyMakerResponse[] | null>(null);
  const [keyMakersError, setKeyMakersError] = useState<string | null>(null);
  const [stockQuery, setStockQuery] = useState("");
  const [stockResults, setStockResults] = useState<StockPhotoResult[] | null>(null);
  const [stockError, setStockError] = useState<string | null>(null);
  const [isSearchingStock, setIsSearchingStock] = useState(false);
  const [imageSourceTab, setImageSourceTab] = useState<"library" | "stock" | "keymaker">("library");
  const [selectedImage, setSelectedImage] = useState<SelectedImage | null>(null);
  const [layoutKey, setLayoutKey] = useState<string>(LAYOUTS[0].key);
  const [layer, setLayer] = useState<TextLayer>({ ...LAYOUTS[0].defaultLayer, text: initialText });
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [imageLoadError, setImageLoadError] = useState<string | null>(null);
  const [saved, setSaved] = useState<ComposedImageResponse | null>(null);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);
  const dragStateRef = useRef<{ dragging: boolean; offsetXPct: number; offsetYPct: number }>({
    dragging: false,
    offsetXPct: 0,
    offsetYPct: 0,
  });

  const layout = LAYOUTS.find((l) => l.key === layoutKey) ?? LAYOUTS[0];

  useEffect(() => {
    listPhotos()
      .then(setPhotos)
      .catch((err) => setPhotosError(err instanceof Error ? err.message : "Failed to load photos."));
    listKeyMakers()
      .then(setKeyMakers)
      .catch((err) => setKeyMakersError(err instanceof Error ? err.message : "Failed to load Key Makers."));
  }, []);

  async function runStockSearch() {
    if (!stockQuery.trim()) return;
    setStockError(null);
    setIsSearchingStock(true);
    try {
      const results = await searchStockPhotos(stockQuery.trim());
      setStockResults(results);
    } catch (err) {
      setStockError(
        err instanceof Error ? err.message : "Stock photo search failed — it may not be configured yet."
      );
    } finally {
      setIsSearchingStock(false);
    }
  }

  // Load the selected image into an <img> once, reused across redraws —
  // redrawing on every layer change shouldn't re-fetch the image.
  //
  // Previously this had no onerror handler: if the new image failed to
  // load (a transient network hiccup, or a host that doesn't actually
  // serve the CORS headers crossOrigin="anonymous" requires — R2 and
  // Pexels both need to send Access-Control-Allow-Origin for this to
  // succeed), onload just never fired. imageRef.current silently kept
  // pointing at whatever was drawn before, so picking a new photo
  // appeared to do nothing — no error, no console message a staff
  // member would ever see, the canvas just didn't change. Now a load
  // failure clears the stale image and surfaces imageLoadError instead
  // of leaving the previous photo on screen unexplained.
  useEffect(() => {
    setImageLoadError(null);
    if (!selectedImage) {
      imageRef.current = null;
      draw();
      return;
    }
    const img = new Image();
    img.crossOrigin = "anonymous"; // needed so canvas.toBlob() isn't tainted by a cross-origin source
    img.onload = () => {
      imageRef.current = img;
      draw();
    };
    img.onerror = () => {
      imageRef.current = null;
      setImageLoadError(
        "Couldn't load that image (it may not allow cross-origin loading) — try a different photo."
      );
      draw();
    };
    img.src = selectedImage.url;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedImage]);

  useEffect(() => {
    draw();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [layer, layoutKey]);

  function selectLayout(key: string) {
    const next = LAYOUTS.find((l) => l.key === key) ?? LAYOUTS[0];
    setLayoutKey(key);
    // Re-center the text at the new layout's default spot — a position
    // dragged to fit the old layout's blocks often lands somewhere odd
    // in the new one (e.g. behind the photo region).
    setLayer((prev) => ({ ...next.defaultLayer, text: prev.text, color: prev.color, fontSizePx: prev.fontSizePx }));
  }

  function draw() {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
    layout.drawFrame(ctx);

    if (imageRef.current && layout.photoRegion) {
      const { x, y, w, h } = layout.photoRegion;
      drawImageCoverInRegion(
        ctx,
        imageRef.current,
        x * CANVAS_WIDTH,
        y * CANVAS_HEIGHT,
        w * CANVAS_WIDTH,
        h * CANVAS_HEIGHT
      );
    }

    if (layer.text.trim()) {
      drawWrappedText(ctx, layer, CANVAS_WIDTH);
    }
  }

  function handlePointerDown(e: React.PointerEvent<HTMLCanvasElement>) {
    const { xPct, yPct } = pointerToCanvasPct(e);
    dragStateRef.current = {
      dragging: true,
      offsetXPct: xPct - layer.xPct,
      offsetYPct: yPct - layer.yPct,
    };
    (e.target as HTMLCanvasElement).setPointerCapture(e.pointerId);
  }

  function handlePointerMove(e: React.PointerEvent<HTMLCanvasElement>) {
    if (!dragStateRef.current.dragging) return;
    const { xPct, yPct } = pointerToCanvasPct(e);
    setLayer((prev) => ({
      ...prev,
      xPct: clamp01(xPct - dragStateRef.current.offsetXPct),
      yPct: clamp01(yPct - dragStateRef.current.offsetYPct),
    }));
  }

  function handlePointerUp() {
    dragStateRef.current.dragging = false;
  }

  function pointerToCanvasPct(e: React.PointerEvent<HTMLCanvasElement>) {
    const rect = e.currentTarget.getBoundingClientRect();
    return {
      xPct: (e.clientX - rect.left) / rect.width,
      yPct: (e.clientY - rect.top) / rect.height,
    };
  }

  async function handleSave() {
    const canvas = canvasRef.current;
    if (!canvas) return;
    setSaveError(null);
    setIsSaving(true);
    try {
      const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, "image/png"));
      if (!blob) throw new Error("Failed to flatten the image — try again.");
      const result = await uploadComposedImage(blob, {
        contentItemId,
        sourcePhotoId: selectedImage?.source === "library" ? selectedImage.photoAssetId : undefined,
      });
      setSaved(result);
      onSaved?.(result);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Failed to save the composed image.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="space-y-3 rounded-md border border-gray-200 bg-gray-50/50 px-4 py-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">
          Photo + Text Overlay
        </span>
        <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-amber-800">
          Prototype — not yet approved
        </span>
      </div>

      <div>
        <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-gray-500">
          Layout
        </span>
        <div className="flex flex-wrap gap-2">
          {LAYOUTS.map((l) => (
            <button
              key={l.key}
              type="button"
              onClick={() => selectLayout(l.key)}
              className={`rounded-md border-2 px-3 py-1.5 text-xs font-semibold transition ${
                layoutKey === l.key
                  ? "border-navy bg-navy text-white"
                  : "border-gray-200 bg-white text-gray-600 hover:border-sky-blue hover:text-navy"
              }`}
            >
              {l.label}
            </button>
          ))}
        </div>
      </div>

      <div>
        <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-gray-500">
          Backdrop photo
        </span>
        <div className="mb-2 flex gap-1 border-b border-gray-200">
          {(
            [
              ["library", "Photo Library"],
              ["stock", "Stock Photos"],
              ["keymaker", "Key Makers"],
            ] as const
          ).map(([tab, label]) => (
            <button
              key={tab}
              type="button"
              onClick={() => setImageSourceTab(tab)}
              className={`-mb-px border-b-2 px-3 py-1.5 text-xs font-semibold transition ${
                imageSourceTab === tab
                  ? "border-navy text-navy"
                  : "border-transparent text-gray-500 hover:text-navy"
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {imageSourceTab === "library" && (
          <>
            {photosError && (
              <div className="mb-2 rounded-md border border-red-300 bg-red-50 px-3 py-2 text-xs text-red-700">
                {photosError}
              </div>
            )}
            {photos && photos.length === 0 && (
              <p className="text-xs text-gray-600">
                No photos in the library yet —{" "}
                <a href="/photos" className="underline">
                  upload one
                </a>{" "}
                first. Real headshots (staff, Key Makers) belong here too.
              </p>
            )}
            {photos && photos.length > 0 && (
              <div className="flex gap-2 overflow-x-auto pb-1">
                {photos.map((photo) => (
                  <button
                    key={photo.id}
                    type="button"
                    onClick={() =>
                      setSelectedImage({ source: "library", url: photo.public_url, photoAssetId: photo.id })
                    }
                    className={`h-16 w-16 shrink-0 overflow-hidden rounded-md border-2 ${
                      selectedImage?.source === "library" && selectedImage.photoAssetId === photo.id
                        ? "border-navy"
                        : "border-gray-200 hover:border-sky-blue"
                    }`}
                    title={photo.filename}
                  >
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={photo.public_url} alt="" className="h-full w-full object-cover" />
                  </button>
                ))}
              </div>
            )}
          </>
        )}

        {imageSourceTab === "stock" && (
          <div className="space-y-2">
            <div className="flex gap-2">
              <input
                type="text"
                value={stockQuery}
                onChange={(e) => setStockQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), runStockSearch())}
                placeholder="e.g. women entrepreneurs meeting"
                className="input flex-1"
              />
              <button
                type="button"
                onClick={runStockSearch}
                disabled={isSearchingStock || !stockQuery.trim()}
                className="rounded-md bg-navy px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-navy/90 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isSearchingStock ? "Searching…" : "Search"}
              </button>
            </div>
            <p className="text-xs text-gray-500">
              Free stock photos via Pexels — licensed for commercial use, no attribution required.
            </p>
            {stockError && (
              <div className="rounded-md border border-red-300 bg-red-50 px-3 py-2 text-xs text-red-700">
                {stockError}
              </div>
            )}
            {stockResults && stockResults.length === 0 && (
              <p className="text-xs text-gray-600">No results — try a different search.</p>
            )}
            {stockResults && stockResults.length > 0 && (
              <div className="flex gap-2 overflow-x-auto pb-1">
                {stockResults.map((photo) => (
                  <button
                    key={photo.id}
                    type="button"
                    onClick={() => setSelectedImage({ source: "stock", url: photo.src_url })}
                    className={`h-16 w-16 shrink-0 overflow-hidden rounded-md border-2 ${
                      selectedImage?.source === "stock" && selectedImage.url === photo.src_url
                        ? "border-navy"
                        : "border-gray-200 hover:border-sky-blue"
                    }`}
                    title={`Photo by ${photo.photographer} on Pexels`}
                  >
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={photo.thumbnail_url} alt={photo.alt} className="h-full w-full object-cover" />
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {imageSourceTab === "keymaker" && (
          <>
            {keyMakersError && (
              <div className="mb-2 rounded-md border border-red-300 bg-red-50 px-3 py-2 text-xs text-red-700">
                {keyMakersError}
              </div>
            )}
            {keyMakers && keyMakers.filter((k) => k.photo_url).length === 0 && (
              <p className="text-xs text-gray-600">
                No Key Maker photos on file yet. Staff/approver headshots (e.g. Nancy, Maria) aren&apos;t
                Key Makers — upload those under the Photo Library tab instead.
              </p>
            )}
            {keyMakers && keyMakers.filter((k) => k.photo_url).length > 0 && (
              <div className="flex gap-2 overflow-x-auto pb-1">
                {keyMakers
                  .filter((k) => k.photo_url)
                  .map((keyMaker) => (
                    <button
                      key={keyMaker.id}
                      type="button"
                      onClick={() =>
                        setSelectedImage({ source: "keymaker", url: keyMaker.photo_url as string })
                      }
                      className={`h-16 w-16 shrink-0 overflow-hidden rounded-md border-2 ${
                        selectedImage?.source === "keymaker" && selectedImage.url === keyMaker.photo_url
                          ? "border-navy"
                          : "border-gray-200 hover:border-sky-blue"
                      }`}
                      title={keyMaker.owner_name}
                    >
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={keyMaker.photo_url as string}
                        alt={keyMaker.owner_name}
                        className="h-full w-full object-cover"
                      />
                    </button>
                  ))}
              </div>
            )}
          </>
        )}
      </div>

      <label className="block">
        <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-gray-500">
          Overlay text
        </span>
        <textarea
          rows={2}
          value={layer.text}
          onChange={(e) => setLayer((prev) => ({ ...prev, text: e.target.value }))}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-sky-blue focus:outline-none focus:ring-2 focus:ring-sky-blue/30"
        />
      </label>

      <div className="flex flex-wrap items-center gap-4">
        <label className="flex items-center gap-2 text-xs text-gray-600">
          Text size
          <input
            type="range"
            min={32}
            max={120}
            value={layer.fontSizePx}
            onChange={(e) => setLayer((prev) => ({ ...prev, fontSizePx: Number(e.target.value) }))}
          />
        </label>
        <label className="flex items-center gap-2 text-xs text-gray-600">
          Text color
          <input
            type="color"
            value={layer.color}
            onChange={(e) => setLayer((prev) => ({ ...prev, color: e.target.value }))}
            className="h-6 w-8 cursor-pointer"
          />
        </label>
      </div>

      {imageLoadError && (
        <div className="rounded-md border border-red-300 bg-red-50 px-3 py-2 text-xs text-red-700">
          {imageLoadError}
        </div>
      )}

      <div
        className="mx-auto overflow-hidden rounded-md border border-gray-300"
        style={{ width: PREVIEW_DISPLAY_SIZE, height: PREVIEW_DISPLAY_SIZE }}
      >
        <canvas
          ref={canvasRef}
          width={CANVAS_WIDTH}
          height={CANVAS_HEIGHT}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerLeave={handlePointerUp}
          className="cursor-move touch-none"
          style={{ width: "100%", height: "100%", display: "block" }}
        />
      </div>
      <p className="text-center text-xs text-gray-500">Drag the text on the preview above to reposition it.</p>

      {saveError && (
        <div className="rounded-md border border-red-300 bg-red-50 px-3 py-2 text-xs text-red-700">
          {saveError}
        </div>
      )}

      {saved ? (
        <p className="text-sm font-semibold text-green-700">Saved — image attached to this post.</p>
      ) : (
        <button
          type="button"
          onClick={handleSave}
          disabled={isSaving}
          className="rounded-md bg-navy px-4 py-2 text-sm font-semibold text-white transition hover:bg-navy/90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isSaving ? "Saving…" : "Save composed image"}
        </button>
      )}
    </div>
  );
}

function clamp01(n: number): number {
  return Math.min(1, Math.max(0, n));
}

/** Draws `img` into the ctx covering the given (x, y, w, h) destination
 * box (like CSS object-fit: cover) — crops rather than
 * stretches/letterboxes, so the photo fills whichever region the
 * active Layout reserves for it (see LAYOUTS' photoRegion). */
function drawImageCoverInRegion(
  ctx: CanvasRenderingContext2D,
  img: HTMLImageElement,
  x: number,
  y: number,
  w: number,
  h: number
) {
  const imgRatio = img.width / img.height;
  const boxRatio = w / h;
  let sx = 0,
    sy = 0,
    sw = img.width,
    sh = img.height;
  if (imgRatio > boxRatio) {
    sw = img.height * boxRatio;
    sx = (img.width - sw) / 2;
  } else {
    sh = img.width / boxRatio;
    sy = (img.height - sh) / 2;
  }
  ctx.drawImage(img, sx, sy, sw, sh, x, y, w, h);
}

/** Smallest font size drawWrappedText will shrink to while trying to
 * fit long text within the canvas — below this it just lets the text
 * run past the edges rather than becoming unreadably tiny. */
const MIN_AUTOFIT_FONT_PX = 22;

/** Draws `layer.text` centered on (xPct, yPct), wrapped to fit within
 * ~90% of the canvas width, with a soft shadow so white text stays
 * legible over busy photo backgrounds without needing a solid block.
 *
 * A long caption at the user's chosen font size can wrap into more
 * lines than fit vertically on the canvas — previously this just drew
 * every line regardless, so the bottom lines could render past the
 * canvas edge and get cut off in the saved PNG. Now it shrinks the
 * font (down to MIN_AUTOFIT_FONT_PX) until the full wrapped block fits
 * within the canvas height, then clamps the block's vertical position
 * so it can't start above the top or run past the bottom even if the
 * user dragged the anchor point close to an edge. */
function drawWrappedText(ctx: CanvasRenderingContext2D, layer: TextLayer, canvasWidth: number) {
  const canvasHeight = ctx.canvas.height;
  const maxWidth = canvasWidth * 0.9;
  const verticalMargin = canvasHeight * 0.04;
  const maxBlockHeight = canvasHeight - verticalMargin * 2;
  const cx = layer.xPct * canvasWidth;

  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.shadowColor = "rgba(0, 0, 0, 0.45)";
  ctx.shadowBlur = 12;

  let fontSizePx = layer.fontSizePx;
  let lines: string[];
  let lineHeight: number;
  // Shrink in steps rather than binary-searching — a handful of
  // iterations is plenty at this size range and keeps the logic simple.
  for (;;) {
    ctx.font = `bold ${fontSizePx}px system-ui, sans-serif`;
    lines = wrapText(ctx, layer.text, maxWidth);
    lineHeight = fontSizePx * 1.2;
    const blockHeight = lines.length * lineHeight;
    if (blockHeight <= maxBlockHeight || fontSizePx <= MIN_AUTOFIT_FONT_PX) break;
    fontSizePx -= 4;
  }

  ctx.fillStyle = layer.color;

  const blockHeight = lines.length * lineHeight;
  const desiredCy = layer.yPct * canvasHeight;
  // Clamp so the text block's own top/bottom edges stay within the
  // margins, regardless of where the user dragged the anchor point.
  const minCy = verticalMargin + blockHeight / 2;
  const maxCy = canvasHeight - verticalMargin - blockHeight / 2;
  const cy = Math.min(Math.max(desiredCy, minCy), Math.max(minCy, maxCy));

  const startY = cy - ((lines.length - 1) * lineHeight) / 2;

  lines.forEach((line, i) => {
    ctx.fillText(line, cx, startY + i * lineHeight);
  });

  ctx.shadowBlur = 0;
}

function wrapText(ctx: CanvasRenderingContext2D, text: string, maxWidth: number): string[] {
  const words = text.split(/\s+/).filter(Boolean);
  const lines: string[] = [];
  let current = "";

  for (const word of words) {
    const candidate = current ? `${current} ${word}` : word;
    if (ctx.measureText(candidate).width > maxWidth && current) {
      lines.push(current);
      current = word;
    } else {
      current = candidate;
    }
  }
  if (current) lines.push(current);
  return lines.length ? lines : [text];
}
