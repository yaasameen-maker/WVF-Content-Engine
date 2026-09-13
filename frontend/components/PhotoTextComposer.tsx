"use client";

import { useEffect, useRef, useState } from "react";
import {
  listPhotos,
  uploadComposedImage,
  type ComposedImageResponse,
  type PhotoAssetResponse,
} from "@/lib/api";

/**
 * Photo + text overlay composer — proposed scope addition, not yet
 * approved by WVF (see backend app/models/media.py's ComposedImage
 * docstring). Lets staff pick a photo from the library, drag a text
 * layer over it (pre-filled with the generated headline/caption), and
 * flatten the result to a PNG entirely in the browser via <canvas> —
 * this component never sends image bytes to the backend until the
 * final flattened PNG is ready to upload. Meant to approximate the
 * "navy/sky-blue block, bold white sans-serif headline" visual pattern
 * from docs/PROJECT_CONTEXT.md's Content Structure Guide, applied over
 * a real staff photo instead of a flat color block.
 *
 * Only mounts once a real ContentItem exists (contentItemId is required,
 * not optional) — a composite always attaches to an already-saved
 * content item, never an in-progress draft, matching how
 * ComposedImageCreate.content_item_id is required server-side too.
 */

const CANVAS_WIDTH = 1080;
const CANVAS_HEIGHT = 1080;

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

export function PhotoTextComposer({
  contentItemId,
  initialText,
}: {
  contentItemId: number;
  initialText: string;
}) {
  const [photos, setPhotos] = useState<PhotoAssetResponse[] | null>(null);
  const [photosError, setPhotosError] = useState<string | null>(null);
  const [selectedPhoto, setSelectedPhoto] = useState<PhotoAssetResponse | null>(null);
  const [layer, setLayer] = useState<TextLayer>({ ...DEFAULT_LAYER, text: initialText });
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saved, setSaved] = useState<ComposedImageResponse | null>(null);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);
  const dragStateRef = useRef<{ dragging: boolean; offsetXPct: number; offsetYPct: number }>({
    dragging: false,
    offsetXPct: 0,
    offsetYPct: 0,
  });

  useEffect(() => {
    listPhotos()
      .then(setPhotos)
      .catch((err) => setPhotosError(err instanceof Error ? err.message : "Failed to load photos."));
  }, []);

  // Load the selected photo into an <img> once, reused across redraws —
  // redrawing on every layer change shouldn't re-fetch the image.
  useEffect(() => {
    if (!selectedPhoto) {
      imageRef.current = null;
      draw();
      return;
    }
    const img = new Image();
    img.crossOrigin = "anonymous"; // R2 bucket is public-read; needed so canvas.toBlob() isn't tainted
    img.onload = () => {
      imageRef.current = img;
      draw();
    };
    img.src = selectedPhoto.public_url;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedPhoto]);

  useEffect(() => {
    draw();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [layer]);

  function draw() {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

    if (imageRef.current) {
      drawImageCover(ctx, imageRef.current, CANVAS_WIDTH, CANVAS_HEIGHT);
      // Subtle navy scrim so white text stays legible over any photo,
      // matching the "bold white sans-serif on a dark block" pattern.
      ctx.fillStyle = "rgba(20, 40, 70, 0.25)";
      ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
    } else {
      ctx.fillStyle = "#4A7EBB";
      ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
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
        sourcePhotoId: selectedPhoto?.id,
      });
      setSaved(result);
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

      {photosError && (
        <div className="rounded-md border border-red-300 bg-red-50 px-3 py-2 text-xs text-red-700">
          {photosError}
        </div>
      )}

      {photos && photos.length === 0 && (
        <p className="text-xs text-gray-600">
          No photos in the library yet —{" "}
          <a href="/photos" className="underline">
            upload one
          </a>{" "}
          first.
        </p>
      )}

      {photos && photos.length > 0 && (
        <div className="flex gap-2 overflow-x-auto pb-1">
          {photos.map((photo) => (
            <button
              key={photo.id}
              type="button"
              onClick={() => setSelectedPhoto(photo)}
              className={`h-16 w-16 shrink-0 overflow-hidden rounded-md border-2 ${
                selectedPhoto?.id === photo.id ? "border-navy" : "border-gray-200 hover:border-sky-blue"
              }`}
              title={photo.filename}
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={photo.public_url} alt="" className="h-full w-full object-cover" />
            </button>
          ))}
        </div>
      )}

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

      <div className="overflow-hidden rounded-md border border-gray-300">
        <canvas
          ref={canvasRef}
          width={CANVAS_WIDTH}
          height={CANVAS_HEIGHT}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerLeave={handlePointerUp}
          className="aspect-square w-full max-w-sm cursor-move touch-none"
        />
      </div>
      <p className="text-xs text-gray-500">Drag the text on the preview above to reposition it.</p>

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

/** Draws `img` into the ctx covering the full w×h box (like CSS
 * object-fit: cover) — crops rather than stretches/letterboxes, so the
 * photo fills the same square frame the review page's other previews use. */
function drawImageCover(ctx: CanvasRenderingContext2D, img: HTMLImageElement, w: number, h: number) {
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
  ctx.drawImage(img, sx, sy, sw, sh, 0, 0, w, h);
}

/** Draws `layer.text` centered on (xPct, yPct), wrapped to fit within
 * ~90% of the canvas width, with a soft shadow so white text stays
 * legible over busy photo backgrounds without needing a solid block. */
function drawWrappedText(ctx: CanvasRenderingContext2D, layer: TextLayer, canvasWidth: number) {
  const maxWidth = canvasWidth * 0.9;
  const cx = layer.xPct * canvasWidth;
  const cy = layer.yPct * ctx.canvas.height;

  ctx.font = `bold ${layer.fontSizePx}px system-ui, sans-serif`;
  ctx.fillStyle = layer.color;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.shadowColor = "rgba(0, 0, 0, 0.45)";
  ctx.shadowBlur = 12;

  const lines = wrapText(ctx, layer.text, maxWidth);
  const lineHeight = layer.fontSizePx * 1.2;
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
