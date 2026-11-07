"use client";

import { useState } from "react";
import type { AnalyzeRequest, Geography, Mode } from "@/lib/types";

const GEOS: readonly { value: Geography; label: string }[] = [
  { value: "us", label: "United States" },
  { value: "india", label: "India" },
  { value: "global", label: "Global" },
];

export default function InputPanel({
  running,
  onRun,
}: {
  running: boolean;
  onRun: (req: AnalyzeRequest) => void;
}) {
  const [mode, setMode] = useState<Mode>("company");
  const [query, setQuery] = useState("");
  const [geography, setGeography] = useState<Geography>("global");
  const [context, setContext] = useState("");
  const [teamSize, setTeamSize] = useState(3);
  const [runway, setRunway] = useState(12);
  const [darkweb, setDarkweb] = useState(true);
  const [advanced, setAdvanced] = useState(false);

  const valid =
    mode === "url"
      ? /^[^\s]+\.[^\s]{2,}$/.test(query.trim()) // a URL needs at least a dot and no spaces
      : query.trim().length >= 2;

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!valid || running) return;
    onRun({
      mode,
      query: query.trim(),
      geography,
      context: context.trim() || undefined,
      team_size: teamSize,
      runway_target_months: runway,
      include_darkweb: darkweb,
    });
  };

  const inputCls =
    "w-full border border-zinc-600 bg-panel/60 px-3 py-2 text-sm text-zinc-200 placeholder-zinc-600";

  return (
    <form
      onSubmit={submit}
      onKeyDown={(e) => {
        // the shortcut is advertised on the panel, not the field — it must
        // survive clicking the market chips or the mode toggle first
        if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) submit(e);
      }}
      className="w-full"
    >
      {/* Mode toggle */}
      <div className="mb-4 grid grid-cols-3 gap-2">
        {(
          [
            { m: "company" as Mode, t: "Company name", d: "type the name" },
            { m: "url" as Mode, t: "Website URL", d: "paste the address" },
            { m: "idea" as Mode, t: "Raw idea", d: "describe the concept" },
          ]
        ).map(({ m, t, d }) => (
          <button
            key={m}
            type="button"
            onClick={() => setMode(m)}
            className={`border px-3 py-3 text-left transition-colors duration-150 ${
              mode === m ? "border-amber-700 bg-amber-950/20" : "border-edge bg-panel/60 hover:border-zinc-600"
            }`}
          >
            <div className={`text-sm font-medium ${mode === m ? "text-amber-400" : "text-zinc-300"}`}>{t}</div>
            <div className="text-[11px] text-zinc-600">{d}</div>
          </button>
        ))}
      </div>

      {/* Query */}
      <textarea
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        rows={2}
        placeholder={
          mode === "company"
            ? "e.g. Rippling, Zoho, Razorpay, ADP…"
            : mode === "url"
              ? "https://stripe.com — the site itself gets read, plus the public registries"
              : "e.g. Payroll compliance automation for Indian SMBs…"
        }
        className={`${inputCls} resize-none leading-relaxed`}
      />

      {/* Geography segmented control */}
      <div className="mt-3 flex flex-wrap items-center gap-3">
        <span className="text-xs text-zinc-500">Market</span>
        <div className="flex border border-edge">
          {GEOS.map((g) => (
            <button
              key={g.value}
              type="button"
              onClick={() => setGeography(g.value)}
              className={`px-3 py-3.5 text-xs transition-colors duration-150 ${
                geography === g.value ? "bg-amber-950/40 text-amber-400" : "text-zinc-500 hover:text-zinc-300"
              }`}
            >
              {g.label}
            </button>
          ))}
        </div>
      </div>

      {/* Advanced */}
      <button type="button" onClick={() => setAdvanced(!advanced)} className="mt-3 flex min-h-[44px] items-center text-xs text-zinc-500 transition-colors duration-150 hover:text-zinc-300">
        {advanced ? "▾" : "▸"} advanced parameters
      </button>
      {advanced && (
        <div className="mt-2 grid grid-cols-1 gap-3 border border-edge bg-panel/40 p-3 sm:grid-cols-3">
          <label className="text-xs text-zinc-500">
            Team size
            <input type="number" min={1} max={200} value={teamSize} onChange={(e) => setTeamSize(Math.max(1, Number(e.target.value) || 1))} className={`mt-1 ${inputCls}`} />
          </label>
          <label className="text-xs text-zinc-500">
            Runway target (months)
            <input type="number" min={1} max={60} value={runway} onChange={(e) => setRunway(Math.min(60, Math.max(1, Number(e.target.value) || 1)))} className={`mt-1 ${inputCls}`} />
          </label>
          <label className="flex items-end gap-2 text-xs text-zinc-500">
            <input type="checkbox" checked={darkweb} onChange={(e) => setDarkweb(e.target.checked)} className="accent-amber-400" />
            <span>
              Tor OSINT module
              <span className="block text-xs text-zinc-600">lawful passive OSINT; degrades without Tor</span>
            </span>
          </label>
          <label className="text-xs text-zinc-500 sm:col-span-3">
            Optional context (sector, ICP, constraints)
            <input value={context} onChange={(e) => setContext(e.target.value)} placeholder="e.g. B2B SaaS for US dental clinics; 2 technical founders" className={`mt-1 ${inputCls}`} />
          </label>
        </div>
      )}

      {/* Run */}
      <button
        type="submit"
        disabled={!valid || running}
        className="mt-5 min-h-[46px] w-full bg-amber-400 px-4 py-2.5 text-sm font-medium text-[color:var(--color-accent-ink)] transition-colors duration-150 enabled:hover:bg-amber-500 disabled:cursor-not-allowed disabled:opacity-55"
      >
        {running ? "Decoding…" : "Run the decode"}
      </button>
      <p className="mt-2 text-xs text-zinc-500">
        Runs entirely on free public sources. ⌘/Ctrl+Enter to launch.
      </p>
    </form>
  );
}
