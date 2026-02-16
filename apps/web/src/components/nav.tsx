"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/search", label: "Search", icon: SearchIcon },
  { href: "/references", label: "References", icon: ReferencesIcon },
  { href: "/generate", label: "Generate", icon: GenerateIcon },
  { href: "/messages", label: "Messages", icon: MessagesIcon },
];

export default function Nav() {
  const pathname = usePathname();

  return (
    <aside className="flex h-screen w-60 flex-col bg-[var(--sidebar-bg)]">
      <div className="px-6 py-7">
        <h1 className="text-[15px] font-semibold tracking-wide text-white">
          Message Writer
        </h1>
      </div>
      <nav className="flex flex-1 flex-col gap-0.5 px-3">
        {links.map(({ href, label, icon: Icon }) => {
          const active = pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`group flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2.5 text-[13px] font-medium transition-all ${
                active
                  ? "bg-[var(--sidebar-active)] text-[var(--sidebar-active-text)]"
                  : "text-[var(--sidebar-text)] hover:bg-white/[0.06] hover:text-white"
              }`}
            >
              <Icon active={active} />
              {label}
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-white/10 px-6 py-4">
        <p className="text-[11px] text-[var(--text-tertiary)]">v1.0</p>
      </div>
    </aside>
  );
}

function SearchIcon({ active }: { active: boolean }) {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className={active ? "text-[var(--sidebar-active-text)]" : "text-[var(--sidebar-text)] group-hover:text-white"}>
      <circle cx="7" cy="7" r="4.5" stroke="currentColor" strokeWidth="1.5" />
      <path d="M10.5 10.5L14 14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

function ReferencesIcon({ active }: { active: boolean }) {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className={active ? "text-[var(--sidebar-active-text)]" : "text-[var(--sidebar-text)] group-hover:text-white"}>
      <rect x="2.5" y="1.5" width="11" height="13" rx="1.5" stroke="currentColor" strokeWidth="1.5" />
      <path d="M5 5h6M5 8h6M5 11h3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

function GenerateIcon({ active }: { active: boolean }) {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className={active ? "text-[var(--sidebar-active-text)]" : "text-[var(--sidebar-text)] group-hover:text-white"}>
      <path d="M8 2v12M4 6l4-4 4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function MessagesIcon({ active }: { active: boolean }) {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className={active ? "text-[var(--sidebar-active-text)]" : "text-[var(--sidebar-text)] group-hover:text-white"}>
      <rect x="1.5" y="2.5" width="13" height="9" rx="1.5" stroke="currentColor" strokeWidth="1.5" />
      <path d="M5 13.5h6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}
