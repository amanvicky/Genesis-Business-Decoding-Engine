"use client";

import { useState } from "react";

export function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <div className={`border border-edge bg-panel/70 ${className}`}>{children}</div>;
}

export function Badge({ tone = "zinc", children }: { tone?: "zinc" | "green" | "red" | "amber" | "cyan"; children: React.ReactNode }) {
  const tones: Record<string, string> = {
    zinc: "border-zinc-700 text-zinc-400",
    green: "border-emerald-700/60 text-emerald-400 bg-emerald-950/30",
    red: "border-red-800/60 text-red-400 bg-red-950/30",
    amber: "border-amber-700/60 text-amber-400 bg-amber-950/30",
    cyan: "border-cyan-800/60 text-cyan-400 bg-cyan-950/30",
  };
  return <span className={`inline-block border px-1.5 py-0.5 text-[11px] leading-4 ${tones[tone]}`}>{children}</span>;
}

export function Sev({ severity }: { severity?: string }) {
  const s = (severity ?? "").toLowerCase();
  if (s === "critical") return <Badge tone="red">Critical</Badge>;
  if (s === "high") return <Badge tone="amber">High</Badge>;
  if (s === "medium") return <Badge tone="cyan">Medium</Badge>;
  if (s === "low") return <Badge>Low</Badge>;
  return <Badge>{severity || "—"}</Badge>;
}

/** Generic keyed-rows table — the workhorse for evidence lists. */
export function Rows<T extends object>({
  rows,
  cols,
  empty = "No data surfaced at this evidence depth.",
}: {
  rows: readonly T[];
  cols: readonly { key: keyof T & string; label: string }[];
  empty?: string;
}) {
  if (!rows.length) return <p className="text-sm text-zinc-500">{empty}</p>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-edge text-xs text-zinc-500">
            {cols.map((c) => (
              <th key={c.key} className="px-2 py-2 font-medium">
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-b border-edge/50 align-top">
              {cols.map((c) => {
                const v: unknown = r[c.key];
                const text =
                  v === null || v === undefined
                    ? ""
                    : typeof v === "object"
                      ? JSON.stringify(v)
                      : String(v);
                return (
                  <td key={c.key} className="px-2 py-2 text-zinc-400">
                    {/^https?:\/\//.test(text) ? (
                      <a href={text} target="_blank" rel="noreferrer" className="text-cyan-500/90 hover:text-cyan-400">
                        source
                      </a>
                    ) : (
                      <span className="line-clamp-3">{text}</span>
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Warn({ children }: { children: React.ReactNode }) {
  return (
    <div className="border border-amber-800/50 bg-amber-950/20 px-3 py-2 text-sm text-amber-300/90">
      {children}
    </div>
  );
}

export function Bullets({ items, className = "" }: { items: readonly string[]; className?: string }) {
  return (
    <ul className={`space-y-1.5 text-sm text-zinc-400 ${className}`}>
      {items.map((t, i) => (
        <li key={i} className="flex gap-2">
          <span className="mt-2 h-1 w-1 shrink-0 bg-zinc-600" />
          <span>{t}</span>
        </li>
      ))}
    </ul>
  );
}

export function CodeBlock({ path, language, content }: { path: string; language?: string; content: string }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };
  return (
    <div className="overflow-hidden border border-edge">
      <div className="flex items-center justify-between border-b border-edge bg-paper-2 px-3 py-1.5">
        <span className="font-mono text-xs text-zinc-500">
          {path} <span className="ml-2 text-zinc-700">{language}</span>
        </span>
        <button onClick={copy} className="min-h-[28px] border border-edge px-3 py-1 text-xs text-zinc-400 transition-colors duration-150 hover:border-amber-700 hover:text-amber-400">
          {copied ? "copied ✓" : "copy"}
        </button>
      </div>
      <pre className="max-h-96 overflow-auto bg-paper px-3 py-3 font-mono text-xs leading-relaxed text-zinc-300">{content}</pre>
    </div>
  );
}

export function KV({ entries }: { entries: readonly (readonly [string, React.ReactNode])[] }) {
  return (
    <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5 text-sm">
      {entries.map(([k, v], i) => (
        <div key={i} className="contents">
          <dt className="text-zinc-500">{k}</dt>
          <dd className="text-zinc-300">{v}</dd>
        </div>
      ))}
    </dl>
  );
}
