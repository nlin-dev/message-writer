"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import type { MessageSummary } from "@/lib/api";
import { getMessages } from "@/lib/api";

export default function MessagesPage() {
  const [messages, setMessages] = useState<MessageSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getMessages()
      .then(setMessages)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load messages"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-sm text-[var(--text-tertiary)]">Loading messages...</p>
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

  if (messages.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <h2 className="text-lg font-semibold text-[var(--text-primary)]">No messages yet</h2>
        <p className="mt-1 text-sm text-[var(--text-tertiary)]">
          Generate your first message from the{" "}
          <Link href="/generate" className="cursor-pointer text-[var(--primary)] hover:underline">
            Generate
          </Link>{" "}
          page.
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="mb-1 text-xl font-semibold text-[var(--text-primary)]">Messages</h1>
      <p className="mb-6 text-sm text-[var(--text-tertiary)]">
        Review and manage your generated messages
      </p>
      <div className="space-y-2">
        {messages.map((msg) => {
          const preview = msg.latest_version.message_text;
          const truncated = preview.length > 150 ? preview.slice(0, 150) + "..." : preview;
          const date = new Date(msg.created_at).toLocaleDateString();

          return (
            <Link
              key={msg.id}
              href={`/messages/${msg.id}`}
              className="group block cursor-pointer rounded-lg border border-[var(--border)] bg-white p-5 transition-all hover:border-[var(--border-hover)] hover:shadow-md"
            >
              <div className="mb-2.5 flex items-center gap-2.5">
                <span
                  className={`inline-block rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${
                    msg.status === "finalized"
                      ? "bg-emerald-50 text-emerald-600"
                      : "bg-[var(--background)] text-[var(--text-tertiary)]"
                  }`}
                >
                  {msg.status}
                </span>
                <span className="text-xs text-[var(--text-tertiary)]">{date}</span>
              </div>
              <p className="text-sm leading-relaxed text-[var(--text-secondary)] transition-colors group-hover:text-[var(--text-primary)]">
                {truncated}
              </p>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
