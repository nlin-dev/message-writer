"use client";

import { useCallback, useEffect, useState } from "react";
import {
  getReferences,
  deleteReference,
  uploadPdf,
} from "@/lib/api";
import type { ReferenceResponse } from "@/lib/api";

export default function ReferencesPage() {
  const [refs, setRefs] = useState<ReferenceResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const fetchRefs = useCallback(async () => {
    try {
      const res = await getReferences();
      setRefs(res.references);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load references");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRefs();
  }, [fetchRefs]);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setError(null);
    try {
      await uploadPdf(file);
      await fetchRefs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("Remove this reference?")) return;

    setDeletingId(id);
    try {
      await deleteReference(id);
      setRefs((prev) => prev.filter((r) => r.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="mb-1 text-xl font-semibold text-[var(--text-primary)]">
        References
      </h1>
      <p className="mb-6 text-sm text-[var(--text-tertiary)]">
        Manage your reference library for message generation
      </p>

      <div className="mb-8 rounded-lg border border-dashed border-[var(--border-hover)] bg-white p-6">
        <p className="mb-3 text-sm font-medium text-[var(--text-secondary)]">
          Upload a PDF document
        </p>
        <label className="inline-flex cursor-pointer items-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--background)] px-4 py-2.5 text-sm font-medium text-[var(--text-secondary)] transition-all hover:border-[var(--border-hover)] hover:bg-white active:scale-[0.98]">
          {uploading ? "Uploading..." : "Choose PDF"}
          <input
            type="file"
            accept=".pdf"
            onChange={handleUpload}
            disabled={uploading}
            className="hidden"
          />
        </label>
      </div>

      {error && (
        <div className="mb-6 rounded-lg border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-600">
          {error}
        </div>
      )}

      {loading ? (
        <div className="py-12 text-center">
          <p className="text-sm text-[var(--text-tertiary)]">Loading references...</p>
        </div>
      ) : refs.length === 0 ? (
        <div className="py-12 text-center">
          <p className="text-sm text-[var(--text-tertiary)]">
            No references yet. Search PubMed or upload a PDF to get started.
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {refs.map((ref) => (
            <div
              key={ref.id}
              className="group flex items-center justify-between rounded-lg border border-[var(--border)] bg-white px-5 py-4 transition-shadow hover:shadow-sm"
            >
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-[var(--text-primary)]">
                  {ref.title}
                </p>
                <div className="mt-1.5 flex items-center gap-2">
                  <span className="inline-flex rounded-md bg-[var(--background)] px-2 py-0.5 text-[11px] font-medium text-[var(--text-tertiary)]">
                    {ref.source}
                  </span>
                  <span className="text-xs text-[var(--text-tertiary)]">{ref.chunk_count} chunks</span>
                  {ref.pmid && <span className="text-xs text-[var(--text-tertiary)]">PMID: {ref.pmid}</span>}
                </div>
              </div>
              <button
                onClick={() => handleDelete(ref.id)}
                disabled={deletingId === ref.id}
                className="ml-4 shrink-0 cursor-pointer rounded-lg px-3 py-1.5 text-xs font-medium text-red-500 opacity-0 transition-all hover:bg-red-50 group-hover:opacity-100 disabled:opacity-50"
              >
                {deletingId === ref.id ? "Removing..." : "Remove"}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
