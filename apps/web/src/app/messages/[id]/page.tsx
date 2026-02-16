"use client";

import { useParams } from "next/navigation";
import { useEffect, useState, useCallback } from "react";
import type { MessageDetail, MessageVersionSchema } from "@/lib/api";
import {
  getMessage,
  getReferences,
  refineMessage,
  editMessage,
  updateMessageStatus,
} from "@/lib/api";
import ClaimsDisplay from "@/components/claims-display";

export default function MessageDetailPage() {
  const params = useParams();
  const id = Number(params.id);

  const [message, setMessage] = useState<MessageDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [refineInstruction, setRefineInstruction] = useState("");
  const [refining, setRefining] = useState(false);

  const [editText, setEditText] = useState("");
  const [editing, setEditing] = useState(false);
  const [editWarnings, setEditWarnings] = useState<string[]>([]);

  const [statusUpdating, setStatusUpdating] = useState(false);
  const [expandedVersion, setExpandedVersion] = useState<number | null>(null);
  const [referenceTitles, setReferenceTitles] = useState<Record<number, string>>({});

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    getMessage(id)
      .then((data) => {
        setMessage(data);
        const latest = data.versions[data.versions.length - 1];
        if (latest) setEditText(latest.message_text);
      })
      .catch((e) => {
        const msg = e instanceof Error ? e.message : "Failed to load message";
        setError(msg);
      })
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    if (!isNaN(id)) load();
    getReferences().then((res) => {
      setReferenceTitles(Object.fromEntries(res.references.map((r) => [r.id, r.title])));
    });
  }, [id, load]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-sm text-[var(--text-tertiary)]">Loading message...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-100 bg-red-50 p-4">
        <p className="text-sm text-red-600">{error}</p>
      </div>
    );
  }

  if (!message) return null;

  const latest = message.versions[message.versions.length - 1];
  const isFinalized = message.status === "finalized";
  const allClaims = [...(latest?.claims ?? []), ...(latest?.dropped_claims ?? [])];

  async function handleStatusToggle() {
    setStatusUpdating(true);
    try {
      const newStatus = isFinalized ? "draft" : "finalized";
      await updateMessageStatus(id, newStatus);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to update status");
    } finally {
      setStatusUpdating(false);
    }
  }

  async function handleRefine() {
    if (!refineInstruction.trim()) return;
    setRefining(true);
    try {
      await refineMessage(id, refineInstruction);
      setRefineInstruction("");
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Refine failed");
    } finally {
      setRefining(false);
    }
  }

  async function handleEdit() {
    if (!editText.trim()) return;
    setEditing(true);
    setEditWarnings([]);
    try {
      const res = await editMessage(id, editText);
      setEditWarnings(res.warnings);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Edit failed");
    } finally {
      setEditing(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-semibold text-[var(--text-primary)]">
            Message #{message.id}
          </h1>
          <span
            className={`inline-block rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${
              isFinalized
                ? "bg-emerald-50 text-emerald-600"
                : "bg-[var(--background)] text-[var(--text-tertiary)]"
            }`}
          >
            {message.status}
          </span>
        </div>
        <button
          onClick={handleStatusToggle}
          disabled={statusUpdating}
          className={`cursor-pointer rounded-lg px-4 py-2 text-sm font-medium transition-all active:scale-[0.98] ${
            isFinalized
              ? "border border-[var(--border)] bg-white text-[var(--text-secondary)] hover:bg-[var(--background)]"
              : "bg-emerald-600 text-white shadow-sm hover:bg-emerald-700"
          } disabled:cursor-not-allowed disabled:opacity-40`}
        >
          {statusUpdating
            ? "Updating..."
            : isFinalized
              ? "Revert to Draft"
              : "Finalize"}
        </button>
      </div>

      {/* Current version text */}
      {latest && (
        <section>
          <h2 className="mb-2 text-sm font-medium text-[var(--text-secondary)]">
            Current Version (v{latest.version_number})
          </h2>
          <div className="rounded-lg border border-[var(--border)] bg-white p-5">
            <p className="whitespace-pre-wrap text-sm leading-relaxed text-[var(--text-primary)]">
              {latest.message_text}
            </p>
          </div>
          {allClaims.length > 0 && (
            <div className="mt-4">
              <h3 className="mb-1.5 text-xs font-medium uppercase tracking-wide text-[var(--text-tertiary)]">Claims</h3>
              <ClaimsDisplay referenceTitles={referenceTitles} claims={allClaims} />
            </div>
          )}
        </section>
      )}

      {/* Refine section */}
      <section>
        <h2 className="mb-2 text-sm font-medium text-[var(--text-secondary)]">Refine</h2>
        <textarea
          value={refineInstruction}
          onChange={(e) => setRefineInstruction(e.target.value)}
          disabled={isFinalized}
          placeholder={
            isFinalized
              ? "Revert to draft to refine"
              : "Enter refinement instruction..."
          }
          rows={3}
          className="w-full rounded-lg border border-[var(--border)] bg-white px-4 py-3 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:border-[var(--primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]/10 disabled:cursor-not-allowed disabled:bg-[var(--background)] disabled:text-[var(--text-tertiary)]"
        />
        <button
          onClick={handleRefine}
          disabled={isFinalized || refining || !refineInstruction.trim()}
          className="mt-2 cursor-pointer rounded-lg bg-[var(--primary)] px-5 py-2 text-sm font-medium text-white shadow-sm transition-all hover:bg-[var(--primary-hover)] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40"
        >
          {refining ? "Refining..." : "Refine"}
        </button>
      </section>

      {/* Edit section */}
      <section>
        <h2 className="mb-2 text-sm font-medium text-[var(--text-secondary)]">Edit</h2>
        <textarea
          value={editText}
          onChange={(e) => setEditText(e.target.value)}
          disabled={isFinalized}
          rows={6}
          className="w-full rounded-lg border border-[var(--border)] bg-white px-4 py-3 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:border-[var(--primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]/10 disabled:cursor-not-allowed disabled:bg-[var(--background)] disabled:text-[var(--text-tertiary)]"
        />
        {editWarnings.length > 0 && (
          <div className="mt-2 rounded-lg border border-amber-200 bg-amber-50 p-3">
            <p className="text-xs font-medium text-amber-800">Grounding warnings:</p>
            <ul className="mt-1 list-inside list-disc text-xs text-amber-700">
              {editWarnings.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          </div>
        )}
        <button
          onClick={handleEdit}
          disabled={isFinalized || editing || !editText.trim()}
          className="mt-2 cursor-pointer rounded-lg bg-[var(--sidebar-bg)] px-5 py-2 text-sm font-medium text-white shadow-sm transition-all hover:bg-[#243044] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40"
        >
          {editing ? "Saving..." : "Save Edit"}
        </button>
      </section>

      {/* Version history */}
      <section>
        <h2 className="mb-3 text-sm font-medium text-[var(--text-secondary)]">
          Version History ({message.versions.length})
        </h2>
        <div className="space-y-2">
          {[...message.versions].reverse().map((v: MessageVersionSchema) => {
            const isExpanded = expandedVersion === v.id;
            const vClaims = [...(v.claims ?? []), ...(v.dropped_claims ?? [])];
            return (
              <div
                key={v.id}
                className="rounded-lg border border-[var(--border)] bg-white transition-shadow hover:shadow-sm"
              >
                <button
                  onClick={() =>
                    setExpandedVersion(isExpanded ? null : v.id)
                  }
                  className="flex w-full cursor-pointer items-center justify-between px-5 py-3.5 text-left transition-colors hover:bg-[var(--background)]"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-medium text-[var(--text-primary)]">
                      v{v.version_number}
                    </span>
                    <span className="rounded-md bg-[var(--background)] px-2 py-0.5 text-[11px] font-medium text-[var(--text-tertiary)]">
                      {v.source}
                    </span>
                    <span className="text-xs text-[var(--text-tertiary)]">
                      {new Date(v.created_at).toLocaleString()}
                    </span>
                  </div>
                  <span className="text-xs text-[var(--text-tertiary)]">
                    {isExpanded ? "collapse" : "expand"}
                  </span>
                </button>
                {isExpanded && (
                  <div className="border-t border-[var(--border)] px-5 py-4">
                    <p className="whitespace-pre-wrap text-sm leading-relaxed text-[var(--text-secondary)]">
                      {v.message_text}
                    </p>
                    {vClaims.length > 0 && (
                      <div className="mt-4">
                        <ClaimsDisplay referenceTitles={referenceTitles} claims={vClaims} />
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
