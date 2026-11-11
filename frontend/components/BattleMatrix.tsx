"use client";

import type { BattleResult, BattleRow } from "@/lib/types";

const GATE_DOTS: Record<string, { color: string; title: string }> = {
  pass: { color: "bg-emerald-500", title: "gates passed" },
  caution: { color: "bg-amber-400", title: "gates cautioned" },
  fail: { color: "bg-red-500", title: "gates failed" },
  pending: { color: "bg-zinc-600", title: "gates unmeasured" },
};

const DECISION_TONE: Record<string, string> = {
  GO: "text-emerald-400",
  CONDITIONAL: "text-amber-400",
  "NO-GO": "text-red-400",
  PENDING: "text-zinc-500",
};

/** The Idea Battle matrix: deterministic columns, rule-based winner highlight,
 * one verdict line. A null winner is rendered honestly as PENDING. */
export default function BattleMatrix({ result }: { result: BattleResult }) {
  const winner = result.winner;
  return (
    <div className="flex flex-col gap-4">
      <div className="border border-edge">
        <div className="flex items-center justify-between border-b border-edge bg-paper-2 px-4 py-2.5">
          <span className="text-xs font-medium uppercase tracking-wide text-zinc-400">Idea battle — the matrix</span>
          <span className="text-[11px] text-zinc-600">decodes ran sequentially · winner is a rule, not an opinion</span>
        </div>
        <div className="divide-y divide-edge/60">
          {result.rows.map((r) => (
            <BattleRowView key={r.i} row={r} won={winner === r.i} tied={winner === null} />
          ))}
        </div>
      </div>

      <div className="border border-edge bg-paper-2 px-4 py-3">
        <div className="flex items-baseline justify-between gap-3">
          <span className="text-xs font-medium uppercase tracking-wide text-zinc-400">
            {winner === null ? "Verdict — pending" : `Verdict — idea ${String.fromCharCode(65 + winner)} leads`}
          </span>
          <span className="text-[11px] text-zinc-600">{result.llm_wrote_prose ? "prose by the local LLM" : "rule-written — LLM offline"}</span>
        </div>
        <p className="mt-2 text-sm leading-relaxed text-zinc-300">{result.prose}</p>
      </div>
    </div>
  );
}

function BattleRowView({ row, won, tied }: { row: BattleRow; won: boolean; tied: boolean }) {
  const g = row.gates;
  return (
    <div className={`flex flex-col gap-3 px-4 py-4 sm:flex-row sm:items-center ${won ? "border-l-2 border-amber-400 bg-amber-950/10" : ""}`}>
      <div className="sm:w-44 sm:shrink-0">
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs text-zinc-600">{row.label}</span>
          {row.kind !== "idea" && <span className="border border-cyan-900/60 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-cyan-400">incumbent</span>}
          {won && <span className="border border-amber-700 bg-amber-950/30 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-amber-400">rule call</span>}
          {tied && <span className="border border-edge px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-zinc-500">pending</span>}
        </div>
        <p className="mt-1 line-clamp-2 text-sm text-zinc-200" title={row.subject}>{row.subject}</p>
        <span className={`mt-1 inline-block text-[11px] ${DECISION_TONE[row.decision] ?? "text-zinc-500"}`}>{row.decision}</span>
      </div>

      <div className="grid flex-1 grid-cols-2 gap-x-6 gap-y-2 sm:grid-cols-4">
        <Stat label="signal score" value={row.score === null || row.score === undefined ? "—" : String(row.score)} tone={scoreTone(row.score)} />
        <Stat label="red-team fatals" value={row.fatals === null || row.fatals === undefined ? "—" : String(row.fatals)} tone={row.fatals && row.fatals >= 3 ? "text-amber-400" : "text-zinc-300"} />
        <Stat label="breakeven" value={row.breakeven === null || row.breakeven === undefined ? "—" : `${row.breakeven.toLocaleString()} cust.`} />
        <Stat label="compliance blockers" value={row.criticals === null || row.criticals === undefined ? "—" : String(row.criticals)} tone={row.criticals ? "text-amber-400" : "text-zinc-300"} />
      </div>

      <div className="flex items-center gap-1.5 sm:shrink-0" title={`${g.pass} pass · ${g.caution} caution · ${g.fail} fail · ${g.pending} pending`}>
        {(["pass", "caution", "fail", "pending"] as const).map((k) => (
          <span key={k} className="flex items-center gap-0.5">
            <span className={`h-1.5 w-1.5 rounded-full ${GATE_DOTS[k]?.color ?? "bg-zinc-600"}`} aria-hidden="true" />
            <span className="font-mono text-[10px] text-zinc-600">{g[k]}</span>
          </span>
        ))}
      </div>
    </div>
  );
}

function Stat({ label, value, tone = "text-zinc-300" }: { label: string; value: string; tone?: string }) {
  return (
    <div>
      <p className="text-[11px] text-zinc-600">{label}</p>
      <p className={`mt-0.5 font-mono text-sm ${tone}`}>{value}</p>
    </div>
  );
}

function scoreTone(score: number | null | undefined): string {
  if (typeof score !== "number") return "text-zinc-500";
  if (score >= 30) return "text-emerald-400";
  if (score >= 15) return "text-amber-400";
  return "text-red-400";
}
