"use client";

import { useEffect, useRef, useState } from "react";
import { deletePhoto, listPhotos, uploadPhoto, type PhotoAssetResponse } from "@/lib/api";

/**
 * Staff photo library — proposed scope addition, not yet approved by
 * WVF (see the image-generation/photo-library plan). Staff upload real
 * event/Key Maker photos here once; AI image generation (once built)
 * will be able to reference them. For now this is just upload + browse
 * + delete — no tagging UI yet (key_maker_id/event_id exist on the
 * backend but aren't wired into this page's form).
 */
export default function PhotosPage() {
  const [photos, setPhotos] = useState<PhotoAssetResponse[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function refresh() {
    listPhotos()
      .then(setPhotos)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load photos."));
  }

  useEffect(refresh, []);

  async function handleFileSelected(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setError(null);
    setIsUploading(true);
    try {
      await uploadPhoto(file);
      refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function handleDelete(photoId: number) {
    setError(null);
    try {
      await deletePhoto(photoId);
      setPhotos((prev) => prev?.filter((p) => p.id !== photoId) ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete photo.");
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold text-navy">Photo Library</h2>
          <p className="text-sm text-gray-600">
            Upload real event and Key Maker photos here for reuse across posts and newsletters.
          </p>
        </div>
        <label className="w-full cursor-pointer rounded-md bg-navy px-4 py-2 text-center text-sm font-semibold text-white transition hover:bg-navy/90 disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto">
          {isUploading ? "Uploading…" : "Upload photo"}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            className="hidden"
            disabled={isUploading}
            onChange={handleFileSelected}
          />
        </label>
      </div>

      {error && (
        <div className="rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
      )}

      {!photos && !error && <p className="text-gray-600">Loading…</p>}

      {photos && photos.length === 0 && (
        <p className="text-gray-600">No photos uploaded yet — click &quot;Upload photo&quot; to add one.</p>
      )}

      {photos && photos.length > 0 && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
          {photos.map((photo) => (
            <PhotoCard key={photo.id} photo={photo} onDelete={() => handleDelete(photo.id)} />
          ))}
        </div>
      )}
    </div>
  );
}

function PhotoCard({ photo, onDelete }: { photo: PhotoAssetResponse; onDelete: () => void }) {
  const [confirmingDelete, setConfirmingDelete] = useState(false);

  return (
    <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
      <div className="flex h-32 w-full items-center justify-center bg-gray-50">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={photo.public_url} alt={photo.filename} className="h-full w-full object-cover" />
      </div>
      <div className="space-y-2 p-3">
        <p className="truncate text-xs font-semibold text-gray-700" title={photo.filename}>
          {photo.filename}
        </p>
        {confirmingDelete ? (
          <div className="flex gap-2 text-xs">
            <button
              type="button"
              onClick={onDelete}
              className="-my-1 inline-block py-1 font-semibold text-red-600 hover:underline"
            >
              Confirm delete
            </button>
            <button
              type="button"
              onClick={() => setConfirmingDelete(false)}
              className="-my-1 inline-block py-1 font-semibold text-gray-500 hover:underline"
            >
              Cancel
            </button>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => setConfirmingDelete(true)}
            className="-my-1 inline-block py-1 text-xs font-semibold text-gray-500 hover:underline"
          >
            Delete
          </button>
        )}
      </div>
    </div>
  );
}
