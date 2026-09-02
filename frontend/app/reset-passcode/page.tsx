"use client";

import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { resetPasscode } from "@/lib/api";

/**
 * Landing page for the emailed "forgot passcode" reset link — see
 * backend app/routers/approvers.py's forgot_passcode/reset_passcode and
 * ApproveButton's "Forgot passcode?" link on the review page. Reads
 * ?token=&approver= from the URL (set when the email was sent) and lets
 * the approver set a new passcode, one time, before the link expires.
 */
function ResetPasscodeForm() {
  const params = useSearchParams();
  const token = params.get("token");
  const approverId = params.get("approver");

  const [newPasscode, setNewPasscode] = useState("");
  const [confirmPasscode, setConfirmPasscode] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  if (!token || !approverId) {
    return (
      <div className="mx-auto max-w-md space-y-3 px-6 py-16 text-center">
        <h1 className="text-xl font-bold text-navy">Invalid reset link</h1>
        <p className="text-sm text-gray-600">
          This link is missing required information. Ask for a new reset link from the Approve
          form on the review page.
        </p>
        <Link href="/" className="text-sm font-semibold text-sky-blue underline">
          Back to WVF Content Engine
        </Link>
      </div>
    );
  }

  if (done) {
    return (
      <div className="mx-auto max-w-md space-y-3 px-6 py-16 text-center">
        <h1 className="text-xl font-bold text-navy">Passcode updated</h1>
        <p className="text-sm text-gray-600">
          Your new passcode is ready to use next time you approve content.
        </p>
        <Link href="/" className="text-sm font-semibold text-sky-blue underline">
          Back to WVF Content Engine
        </Link>
      </div>
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (newPasscode !== confirmPasscode) {
      setError("Passcodes don't match.");
      return;
    }
    if (newPasscode.length < 6) {
      setError("Passcode must be at least 6 characters.");
      return;
    }

    setIsSubmitting(true);
    try {
      await resetPasscode(Number(approverId), token as string, newPasscode);
      setDone(true);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "This reset link is invalid or has expired — ask for a new one."
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-md px-6 py-16">
      <h1 className="mb-1 text-xl font-bold text-navy">Set a new passcode</h1>
      <p className="mb-6 text-sm text-gray-600">
        This link works once. Choose a new passcode for approving content.
      </p>
      <form onSubmit={handleSubmit} className="space-y-4">
        <label className="block">
          <span className="mb-1 block text-sm font-medium text-navy">New passcode</span>
          <input
            required
            type="password"
            minLength={6}
            value={newPasscode}
            onChange={(e) => setNewPasscode(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-sky-blue focus:outline-none focus:ring-2 focus:ring-sky-blue/30"
          />
        </label>
        <label className="block">
          <span className="mb-1 block text-sm font-medium text-navy">Confirm passcode</span>
          <input
            required
            type="password"
            minLength={6}
            value={confirmPasscode}
            onChange={(e) => setConfirmPasscode(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-sky-blue focus:outline-none focus:ring-2 focus:ring-sky-blue/30"
          />
        </label>
        {error && (
          <div className="rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}
        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full rounded-md bg-navy px-4 py-2 text-sm font-semibold text-white transition hover:bg-navy/90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isSubmitting ? "Saving…" : "Set new passcode"}
        </button>
      </form>
    </div>
  );
}

export default function ResetPasscodePage() {
  return (
    <Suspense fallback={null}>
      <ResetPasscodeForm />
    </Suspense>
  );
}
