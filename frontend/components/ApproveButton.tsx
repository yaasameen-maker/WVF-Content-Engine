"use client";

import { useState } from "react";
import { approveContentItem, requestPasscodeReset } from "@/lib/api";

/**
 * Explicit sign-off action — moves a content item from draft to approved
 * (see POST /api/content/{id}/approve). This is the single-approver
 * (Nancy/Maria) confirmation step described in docs/PROJECT_CONTEXT.md;
 * it does not post/send anything — "Post to X" stays a separate manual
 * click. Passcode-gated (see backend app/models/approver.py) so approval
 * records who actually signed off, which matters now that approval is
 * the hard gate before scheduled auto-posting to X.
 *
 * Shared between the review page (right after generating/picking
 * content) and ContentItemDetailModal (anything already saved, e.g. a
 * scheduled template post that never passed through /review at all) —
 * those were previously the only two places content is shown, and only
 * the first had an Approve action, so anything saved via "Schedule this
 * post" had no path to ever being approved.
 */
export function ApproveButton({
  contentItemId,
  initialStatus = "draft",
  initialApprovedByName = null,
}: {
  contentItemId: number;
  initialStatus?: string;
  initialApprovedByName?: string | null;
}) {
  const [status, setStatus] = useState<"draft" | "approved">(
    initialStatus === "approved" ? "approved" : "draft"
  );
  const [approvedByName, setApprovedByName] = useState<string | null>(initialApprovedByName);
  const [formOpen, setFormOpen] = useState(false);
  const [approverName, setApproverName] = useState("");
  const [passcode, setPasscode] = useState("");
  const [isApproving, setIsApproving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resetRequested, setResetRequested] = useState(false);
  const [isRequestingReset, setIsRequestingReset] = useState(false);

  async function handleApprove(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setIsApproving(true);
    try {
      const updated = await approveContentItem(contentItemId, approverName, passcode);
      setStatus(updated.status === "approved" ? "approved" : "draft");
      setApprovedByName(updated.approved_by_name);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to approve — check the name and passcode.");
    } finally {
      setIsApproving(false);
    }
  }

  async function handleForgotPasscode() {
    if (!approverName.trim()) {
      setError('Type your name first, then click "Forgot passcode?"');
      return;
    }
    setError(null);
    setIsRequestingReset(true);
    try {
      await requestPasscodeReset(approverName.trim());
      setResetRequested(true);
    } catch {
      // Deliberately generic — same as the backend's response shape, so
      // this never reveals whether the name matched a real approver.
      setResetRequested(true);
    } finally {
      setIsRequestingReset(false);
    }
  }

  if (status === "approved") {
    return (
      <p className="rounded-md border border-green-300 bg-green-50 px-4 py-3 text-sm font-semibold text-green-700">
        ✓ Approved{approvedByName ? ` by ${approvedByName}` : ""}
      </p>
    );
  }

  if (!formOpen) {
    return (
      <button
        type="button"
        onClick={() => setFormOpen(true)}
        className="rounded-md bg-green-700 px-4 py-2 text-sm font-semibold text-white transition hover:bg-green-800"
      >
        Approve
      </button>
    );
  }

  return (
    <form
      onSubmit={handleApprove}
      className="flex flex-wrap items-end gap-3 rounded-md border border-gray-200 bg-gray-50/50 px-4 py-3"
    >
      <label className="block">
        <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-gray-500">Name</span>
        <input
          required
          type="text"
          value={approverName}
          onChange={(e) => setApproverName(e.target.value)}
          placeholder="Nancy or Maria"
          className="w-36 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-sky-blue focus:outline-none focus:ring-2 focus:ring-sky-blue/30"
        />
      </label>
      <label className="block">
        <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-gray-500">
          Passcode
        </span>
        <input
          required
          type="password"
          value={passcode}
          onChange={(e) => setPasscode(e.target.value)}
          className="w-36 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-sky-blue focus:outline-none focus:ring-2 focus:ring-sky-blue/30"
        />
      </label>
      <button
        type="submit"
        disabled={isApproving}
        className="rounded-md bg-green-700 px-4 py-2 text-sm font-semibold text-white transition hover:bg-green-800 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isApproving ? "Approving…" : "Confirm Approval"}
      </button>
      <button
        type="button"
        onClick={() => setFormOpen(false)}
        className="text-xs font-semibold text-gray-500 hover:underline"
      >
        Cancel
      </button>
      {!resetRequested ? (
        <button
          type="button"
          onClick={handleForgotPasscode}
          disabled={isRequestingReset}
          className="text-xs font-semibold text-sky-blue hover:underline disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isRequestingReset ? "Sending…" : "Forgot passcode?"}
        </button>
      ) : (
        <p className="text-xs text-gray-600">
          If that name has an email on file, a reset link was sent to it.
        </p>
      )}
      {error && <p className="w-full text-xs text-red-600">{error}</p>}
    </form>
  );
}
