"use client";

import { useEffect, useRef, useState } from "react";
import { streamGenerate } from "@/lib/api";
import type { GenerateRequest, GenerateResponse } from "@/lib/api";

const STAGES = ["Retrieving", "Generating", "Verifying", "Persisting", "Done"] as const;
const STAGE_KEYS = ["retrieving", "generating", "verifying", "persisting", "done"] as const;

function extractClaimTexts(json: string): string {
  try {
    const parsed = JSON.parse(json);
    if (parsed?.claims && Array.isArray(parsed.claims)) {
      return parsed.claims
        .map((c: { text?: string }) => c.text ?? "")
        .filter(Boolean)
        .join(" ");
    }
  } catch {
    // Partial JSON — extract text values with regex
    const texts: string[] = [];
    const re = /"text"\s*:\s*"((?:[^"\\]|\\.)*)"/g;
    let match;
    while ((match = re.exec(json)) !== null) {
      texts.push(match[1].replace(/\\"/g, '"').replace(/\\n/g, "\n"));
    }
    return texts.join(" ");
  }
  return "";
}

interface StreamViewerProps {
  request: GenerateRequest;
  onComplete: (response: GenerateResponse) => void;
}

export default function StreamViewer({ request, onComplete }: StreamViewerProps) {
  const [stage, setStage] = useState<string>("retrieving");
  const [rawJson, setRawJson] = useState("");
  const [error, setError] = useState<string | null>(null);
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;

    (async () => {
      try {
        for await (const event of streamGenerate(request)) {
          const data = event.data as Record<string, unknown>;

          switch (event.event) {
            case "status":
              setStage(data.stage as string);
              break;
            case "delta":
              setRawJson((prev) => prev + (data.text as string));
              break;
            case "final":
              setStage("done");
              onComplete(data as unknown as GenerateResponse);
              return;
            case "error":
              setError(data.detail as string);
              return;
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Stream failed");
      }
    })();
  }, [request, onComplete]);

  const stageIndex = STAGE_KEYS.indexOf(stage as typeof STAGE_KEYS[number]);
  const displayText = rawJson ? extractClaimTexts(rawJson) : "";

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4 rounded-lg border border-[var(--border)] bg-white px-5 py-3">
        {STAGES.map((label, i) => (
          <div key={label} className="flex items-center gap-2">
            <div
              className={`h-2 w-2 rounded-full transition-colors ${
                i < stageIndex
                  ? "bg-emerald-500"
                  : i === stageIndex && stage !== "done"
                    ? "animate-pulse bg-[var(--primary)]"
                    : i === stageIndex
                      ? "bg-emerald-500"
                      : "bg-[var(--border)]"
              }`}
            />
            <span className={`text-xs transition-colors ${
              i <= stageIndex ? "font-medium text-[var(--text-primary)]" : "text-[var(--text-tertiary)]"
            }`}>{label}</span>
          </div>
        ))}
      </div>

      {error && (
        <div className="rounded-lg border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-600">
          {error}
        </div>
      )}

      {stage === "generating" && !displayText && (
        <div className="rounded-lg border border-[var(--border)] bg-white p-5 text-sm text-[var(--text-tertiary)]">
          Generating message...
        </div>
      )}

      {displayText && stage !== "done" && (
        <div className="rounded-lg border border-[var(--border)] bg-white p-5 text-sm leading-relaxed text-[var(--text-primary)] whitespace-pre-wrap">
          {displayText}
          {stage === "generating" && (
            <span className="ml-1 inline-block h-4 w-0.5 animate-pulse bg-[var(--primary)]" />
          )}
        </div>
      )}
    </div>
  );
}
