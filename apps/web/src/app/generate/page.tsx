"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { getReferences } from "@/lib/api";
import type {
  GenerateRequest,
  GenerateResponse,
  ReferenceResponse,
} from "@/lib/api";
import ClaimsDisplay from "@/components/claims-display";
import StreamViewer from "@/components/stream-viewer";

export default function GeneratePage() {
  const [prompt, setPrompt] = useState("");
  const [refs, setRefs] = useState<ReferenceResponse[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [streamRequest, setStreamRequest] = useState<GenerateRequest | null>(null);

  useEffect(() => {
    getReferences().then((res) => {
      setRefs(res.references);
      setSelectedIds(new Set(res.references.map((r) => r.id)));
    });
  }, []);

  function toggleRef(id: number) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  const handleComplete = useCallback((response: GenerateResponse) => {
    setResult(response);
    setStreamRequest(null);
  }, []);

  function handleGenerate() {
    if (!prompt.trim() || selectedIds.size === 0) return;

    setResult(null);
    setStreamRequest({
      prompt: prompt.trim(),
      reference_ids: Array.from(selectedIds),
    });
  }

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="mb-1 text-xl font-semibold text-[var(--text-primary)]">
        Generate Message
      </h1>
      <p className="mb-6 text-sm text-[var(--text-tertiary)]">
        Create a grounded message from your selected references
      </p>

      <div className="mb-6 space-y-5">
        <div>
          <label className="mb-2 block text-sm font-medium text-[var(--text-secondary)]">
            Prompt
          </label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={4}
            placeholder="Describe the message you want to generate..."
            className="w-full rounded-lg border border-[var(--border)] bg-white px-4 py-3 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:border-[var(--primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]/10"
          />
        </div>

        <div>
          <label className="mb-2 block text-sm font-medium text-[var(--text-secondary)]">
            References
          </label>
          {refs.length === 0 ? (
            <p className="text-sm text-[var(--text-tertiary)]">
              No references available.{" "}
              <Link href="/references" className="cursor-pointer text-[var(--primary)] hover:underline">
                Add some first.
              </Link>
            </p>
          ) : (
            <div className="max-h-48 space-y-1 overflow-y-auto rounded-lg border border-[var(--border)] bg-white p-3">
              {refs.map((ref) => (
                <label
                  key={ref.id}
                  className="flex cursor-pointer items-center gap-2.5 rounded-md px-2.5 py-2 text-sm transition-colors hover:bg-[var(--background)]"
                >
                  <input
                    type="checkbox"
                    checked={selectedIds.has(ref.id)}
                    onChange={() => toggleRef(ref.id)}
                    className="cursor-pointer rounded border-[var(--border)] text-[var(--primary)] focus:ring-[var(--primary)]"
                  />
                  <span className="truncate text-[var(--text-primary)]">{ref.title}</span>
                  <span className="ml-auto shrink-0 text-xs text-[var(--text-tertiary)]">
                    {ref.chunk_count} chunks
                  </span>
                </label>
              ))}
            </div>
          )}
        </div>

        <div className="flex justify-end">
          <button
            onClick={handleGenerate}
            disabled={!!streamRequest || !prompt.trim() || selectedIds.size === 0}
            className="cursor-pointer rounded-lg bg-[var(--primary)] px-6 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-[var(--primary-hover)] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40"
          >
            Generate
          </button>
        </div>
      </div>

      {streamRequest && (
        <StreamViewer request={streamRequest} onComplete={handleComplete} />
      )}

      {result && (
        <div className="mt-8 space-y-5">
          <div className="rounded-lg border border-[var(--border)] bg-white p-6">
            <h2 className="mb-3 text-sm font-semibold text-[var(--text-secondary)]">
              Generated Message
            </h2>
            <p className="text-sm leading-relaxed text-[var(--text-primary)] whitespace-pre-wrap">
              {result.message_text}
            </p>
          </div>

          <ClaimsDisplay
            claims={result.claims}
            referenceTitles={Object.fromEntries(refs.map((r) => [r.id, r.title]))}
          />

          {result.warnings.length > 0 && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3">
              <h3 className="mb-1 text-sm font-semibold text-amber-800">
                Warnings
              </h3>
              <ul className="list-inside list-disc text-sm text-amber-700">
                {result.warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          {result.message_id && (
            <Link
              href={`/messages/${result.message_id}`}
              className="inline-flex cursor-pointer items-center rounded-lg border border-[var(--primary)] px-4 py-2 text-sm font-medium text-[var(--primary)] transition-colors hover:bg-[var(--primary-light)] active:scale-[0.98]"
            >
              View Message
            </Link>
          )}
        </div>
      )}
    </div>
  );
}
