import type { Claim } from "@/lib/api";

interface ClaimsDisplayProps {
  claims: Claim[];
  referenceTitles?: Record<number, string>;
}

export default function ClaimsDisplay({ claims, referenceTitles = {} }: ClaimsDisplayProps) {
  if (claims.length === 0) return null;

  const supported = claims.filter((c) => c.status === "supported");
  const dropped = claims.filter((c) => c.status === "dropped");

  return (
    <div className="space-y-2.5">
      <h3 className="text-sm font-semibold text-[var(--text-secondary)]">
        Claims ({supported.length} supported
        {dropped.length > 0 && `, ${dropped.length} dropped`})
      </h3>
      {claims.map((claim, i) => {
        const isDropped = claim.status === "dropped";
        return (
          <div
            key={i}
            className={`rounded-lg border px-4 py-3 text-sm ${
              isDropped
                ? "border-red-200 border-l-4 border-l-red-400 bg-red-50/50 opacity-70"
                : "border-[var(--border)] bg-white"
            }`}
          >
            <p className={isDropped ? "text-[var(--text-tertiary)]" : "text-[var(--text-secondary)]"}>
              {claim.text}
              {claim.citations.map((c, j) => (
                <span key={j} className="group relative ml-0.5 inline-block">
                  <span className="cursor-help rounded bg-[var(--primary-light)] px-1 py-0.5 text-xs font-medium text-[var(--primary)]">
                    [{c.reference_id}]
                  </span>
                  {referenceTitles[c.reference_id] && (
                    <span className="pointer-events-none absolute bottom-full left-1/2 z-10 mb-1.5 max-w-sm -translate-x-1/2 rounded-lg bg-[var(--sidebar-bg)] px-3 py-2 text-xs leading-snug text-white opacity-0 shadow-lg transition-opacity group-hover:opacity-100">
                      {referenceTitles[c.reference_id]}
                      <span className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-[var(--sidebar-bg)]" />
                    </span>
                  )}
                </span>
              ))}
            </p>
            {isDropped && claim.warning && (
              <p className="mt-1.5 text-xs font-medium text-amber-600">
                {claim.warning}
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}
