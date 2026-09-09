"use client";

import { useEffect, useState } from "react";
import {
  disconnectX,
  getXConnectionStatus,
  getXConnectStartUrl,
  postToX,
  updateContentItemBody,
} from "@/lib/api";

/**
 * Manual-click "Post to X" — connects the account if needed, saves
 * whatever body is currently on screen (so a staff edit isn't silently
 * dropped), then publishes it. Never fires on its own; only in direct
 * response to a click. See docs/STATUS_AND_SCOPE.md's Aug 8 manual-click
 * scope decision, and app/routers/social.py's run_scheduled_x_posts for
 * the separate scheduled-auto-post path this doesn't touch.
 *
 * Shared between the review page (right after generating, with the
 * currently-edited caption/CTA) and ContentItemDetailModal (anything
 * already saved, e.g. a stale approved-but-never-auto-posted item —
 * same reasoning as ApproveButton's extraction: this used to be the
 * only place with a Post to X action, so anything viewed from /calendar
 * had no way to be manually posted at all).
 */
export function PostToXButton({
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
      // Save whatever's currently on screen before posting, so "Post to
      // X" publishes the current state, not stale/original text if it's
      // since been edited.
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
            className="-my-2 inline-block py-2 text-xs font-semibold text-gray-500 hover:underline"
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
