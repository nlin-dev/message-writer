"use client";

import { useState } from "react";
import { searchPubMed, addFromPubMed } from "@/lib/api";
import type { PubMedResult } from "@/lib/api";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<PubMedResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [addedPmids, setAddedPmids] = useState<Set<string>>(new Set());
  const [addingPmid, setAddingPmid] = useState<string | null>(null);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const res = await searchPubMed(query.trim());
      setResults(res.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleAdd(pmid: string) {
    setAddingPmid(pmid);
    try {
      await addFromPubMed(pmid);
      setAddedPmids((prev) => new Set(prev).add(pmid));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add reference");
    } finally {
      setAddingPmid(null);
    }
  }

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="mb-1 text-xl font-semibold text-[var(--text-primary)]">
        PubMed Search
      </h1>
      <p className="mb-6 text-sm text-[var(--text-tertiary)]">
        Find and add research articles to your working set
      </p>

      <form onSubmit={handleSearch} className="mb-8 flex gap-3">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search PubMed for articles..."
          className="flex-1 rounded-lg border border-[var(--border)] bg-white px-4 py-2.5 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:border-[var(--primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]/10"
        />
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="cursor-pointer rounded-lg bg-[var(--primary)] px-5 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-[var(--primary-hover)] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40"
        >
          {loading ? "Searching..." : "Search"}
        </button>
      </form>

      {error && (
        <div className="mb-6 rounded-lg border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-600">
          {error}
        </div>
      )}

      {!loading && results.length === 0 && query && !error && (
        <div className="py-12 text-center">
          <p className="text-sm text-[var(--text-tertiary)]">No results found for your query.</p>
        </div>
      )}

      <div className="space-y-3">
        {results.map((r) => (
          <div
            key={r.pmid}
            className="rounded-lg border border-[var(--border)] bg-white p-5 transition-shadow hover:shadow-md"
          >
            <div className="mb-3 flex items-start justify-between gap-4">
              <h2 className="text-sm font-semibold leading-snug text-[var(--text-primary)]">
                {r.title}
              </h2>
              <button
                onClick={() => handleAdd(r.pmid)}
                disabled={addedPmids.has(r.pmid) || addingPmid === r.pmid}
                className={`shrink-0 cursor-pointer rounded-lg px-3.5 py-1.5 text-xs font-medium transition-all active:scale-[0.97] ${
                  addedPmids.has(r.pmid)
                    ? "cursor-default border border-emerald-200 bg-emerald-50 text-emerald-600"
                    : "border border-[var(--primary)] text-[var(--primary)] hover:bg-[var(--primary-light)] disabled:cursor-wait disabled:opacity-50"
                }`}
              >
                {addedPmids.has(r.pmid)
                  ? "Added"
                  : addingPmid === r.pmid
                    ? "Adding..."
                    : "Add to Working Set"}
              </button>
            </div>
            <p className="mb-1 text-xs text-[var(--text-secondary)]">
              {r.authors.join(", ")}
            </p>
            <p className="mb-3 text-xs text-[var(--text-tertiary)]">
              PMID: {r.pmid} &middot; {r.pub_date}
            </p>
            <p className="text-[13px] leading-relaxed text-[var(--text-secondary)]">
              {r.abstract.length > 300
                ? r.abstract.slice(0, 300) + "..."
                : r.abstract}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
