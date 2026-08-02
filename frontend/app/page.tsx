"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { generateContent, type EventInput } from "@/lib/api";

const EMPTY_EVENT: EventInput = {
  title: "",
  date: "",
  speaker: "",
  registration_link: "",
  audience: "",
  description: "",
};

export default function EventFormPage() {
  const router = useRouter();
  const [event, setEvent] = useState<EventInput>(EMPTY_EVENT);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function updateField(field: keyof EventInput, value: string) {
    setEvent((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setIsGenerating(true);

    try {
      const result = await generateContent(event);
      sessionStorage.setItem("wvf_generated_content", JSON.stringify(result));
      sessionStorage.setItem("wvf_source_event", JSON.stringify(event));
      router.push("/review");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong generating content.");
    } finally {
      setIsGenerating(false);
    }
  }

  return (
    <div>
      <h2 className="mb-1 text-2xl font-bold text-navy">New Event Campaign</h2>
      <p className="mb-6 text-sm text-gray-600">
        Enter event details to generate a complete WVF-branded marketing campaign.
      </p>

      <form onSubmit={handleSubmit} className="space-y-5">
        <Field label="Event Title">
          <input
            required
            type="text"
            value={event.title}
            onChange={(e) => updateField("title", e.target.value)}
            className="input"
            placeholder="Money & Credit: Understanding Your Credit Report"
          />
        </Field>

        <Field label="Date">
          <input
            required
            type="text"
            value={event.date}
            onChange={(e) => updateField("date", e.target.value)}
            className="input"
            placeholder="August 15, 2026 at 2:00 PM ET"
          />
        </Field>

        <Field label="Speaker">
          <input
            required
            type="text"
            value={event.speaker}
            onChange={(e) => updateField("speaker", e.target.value)}
            className="input"
            placeholder="WVF Financial Education Team"
          />
        </Field>

        <Field label="Registration Link">
          <input
            required
            type="url"
            value={event.registration_link}
            onChange={(e) => updateField("registration_link", e.target.value)}
            className="input"
            placeholder="https://www.womenventurefund.org/events/..."
          />
        </Field>

        <Field label="Target Audience">
          <input
            required
            type="text"
            value={event.audience}
            onChange={(e) => updateField("audience", e.target.value)}
            className="input"
            placeholder="NYC-based women entrepreneurs, Spanish-speaking community welcome"
          />
        </Field>

        <Field label="Description">
          <textarea
            required
            rows={5}
            value={event.description}
            onChange={(e) => updateField("description", e.target.value)}
            className="input"
            placeholder="Describe the event, what attendees will learn, and any relevant details..."
          />
        </Field>

        {error && (
          <div className="rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={isGenerating}
          className="rounded-md bg-navy px-6 py-3 font-semibold text-white transition hover:bg-navy/90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isGenerating ? "Generating campaign…" : "Generate Campaign"}
        </button>
      </form>

      <style jsx global>{`
        .input {
          width: 100%;
          border: 1px solid #d1d5db;
          border-radius: 0.375rem;
          padding: 0.5rem 0.75rem;
          font-size: 0.95rem;
        }
        .input:focus {
          outline: none;
          border-color: #6fa8dc;
          box-shadow: 0 0 0 2px rgba(111, 168, 220, 0.3);
        }
      `}</style>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-navy">{label}</span>
      {children}
    </label>
  );
}
