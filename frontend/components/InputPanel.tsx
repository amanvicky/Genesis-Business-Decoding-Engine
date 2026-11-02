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

  const valid = query.trim().length >= 2;

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

  return (
    <form onSubmit={submit} className="mx-auto w-full max-w-2xl">
      {/* Mode toggle */}
      <div className="mb-4 grid grid-cols-2 gap-2">
        {(
          [
            { m: "company" as Mode, t: "Decode a company", s: "ADP, Stripe, a competitor…" },
            { m: "idea" as Mode, t: "Validate a raw idea", s: "describe the business in a sentence" },
          ]
        ).map(({ m, t, s }) => (
          <button
            key={m}
            type="button"
            onClick={() => setMode(m)}
            className={`rounded-lg border px-4 py-3 text-left transition-all duration-200 ${
              mode === m ? "border-emerald-700/70 bg-emerald-950/20" : "border-edge bg-panel/60 hover:border-zinc-700"
            }`}
          >
            <div className={`text-sm font-medium ${mode === m ? "text-emerald-400" : "text-zinc-300"}`}>{t}</div>
            <div className="mt-0.5 text-xs text-zinc-600">{s}</div>
          </button>
        ))}
      </div>

      {/* Query */}
      <textarea
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) submit(e);
        }}
        rows={2}
        placeholder={mode === "company" ? "e.g. Rippling, Zoho, Razorpay, ADP…" : "e.g. Payroll compliance automation for Indian SMBs…"}
        className="w-full resize-none rounded-lg border border-edge bg-panel/60 px-4 py-3 text-sm text-zinc-200 placeholder-zinc-600 outline-none transition-colors duration-200 focus:border-emerald-800/70"
      />

      {/* Geography segmented control */}
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <span className="text-xs uppercase tracking-wider text-zinc-600">Market</span>
        <div className="flex overflow-hidden rounded-md border border-edge">
          {GEOS.map((g) => (
            <button
              key={g.value}
              type="button"
              onClick={() => setGeography(g.value)}
              className={`px-3 py-1.5 text-xs transition-colors duration-150 ${
                geography === g.value ? "bg-emerald-950/40 text-emerald-400" : "text-zinc-500 hover:text-zinc-300"
              }`}
            >
              {g.label}
            </button>
          ))}
        </div>
      </div>

      {/* Advanced */}
      <button type="button" onClick={() => setAdvanced(!advanced)} className="mt-3 text-xs text-zinc-600 transition-colors hover:text-zinc-400">
        {advanced ? "▾" : "▸"} advanced parameters
      </button>
      {advanced && (
        <div className="mt-2 grid grid-cols-1 gap-3 rounded-lg border border-edge bg-panel/40 p-3 sm:grid-cols-3">
          <label className="text-xs text-zinc-500">
            Team size
            <input type="number" min={1} max={200} value={teamSize} onChange={(e) => setTeamSize(Math.max(1, Number(e.target.value) || 1))} className="mt-1 w-full rounded border border-edge bg-base px-2 py-1.5 text-sm text-zinc-200 outline-none focus:border-emerald-800/70" />
          </label>
          <label className="text-xs text-zinc-500">
            Runway target (months)
            <input type="number" min={1} max={60} value={runway} onChange={(e) => setRunway(Math.min(60, Math.max(1, Number(e.target.value) || 1)))} className="mt-1 w-full rounded border border-edge bg-base px-2 py-1.5 text-sm text-zinc-200 outline-none focus:border-emerald-800/70" />
          </label>
          <label className="flex items-end gap-2 text-xs text-zinc-500">
            <input type="checkbox" checked={darkweb} onChange={(e) => setDarkweb(e.target.checked)} className="accent-emerald-600" />
            <span>
              Tor OSINT module
              <span className="block text-[10px] text-zinc-700">lawful passive OSINT; degrades without Tor</span>
            </span>
          </label>
          <label className="text-xs text-zinc-500 sm:col-span-3">
            Optional context (sector, ICP, constraints)
            <input value={context} onChange={(e) => setContext(e.target.value)} placeholder="e.g. B2B SaaS for US dental clinics; 2 technical founders" className="mt-1 w-full rounded border border-edge bg-base px-2 py-1.5 text-sm text-zinc-200 placeholder-zinc-700 outline-none focus:border-emerald-800/70" />
          </label>
        </div>
      )}

      {/* Run */}
      <button
        type="submit"
        disabled={!valid || running}
        className="mt-5 w-full rounded-lg border border-emerald-800/70 bg-emerald-950/30 py-3 text-sm font-medium tracking-wide text-emerald-400 transition-all duration-200 enabled:hover:border-emerald-600 enabled:hover:bg-emerald-900/30 disabled:cursor-not-allowed disabled:opacity-40"
      >
        {running ? "DECODE IN PROGRESS…" : "RUN GENESIS DECODE"}
      </button>
      <p className="mt-2 text-center text-[11px] text-zinc-700">
        Runs entirely on free public sources · ⌘/Ctrl+Enter to launch
      </p>
    </form>
  );
}
