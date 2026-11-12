"use client";

import type { AdversaryChallenge, AdversaryData } from "@/lib/types";
import { Badge, Bullets, Card } from "@/components/ui";
import { LLMInsight } from "./AnalysisTabs";

const SEV_TONE: Record<string, string> = {
  fatal: "border-red-800/60 text-red-400 bg-red-950/30",
  serious: "border-amber-700/60 text-amber-400 bg-amber-950/30",
  probe: "border-cyan-800/60 text-cyan-400 bg-cyan-950/30",
};

function Challenge({ k }: { k: AdversaryChallenge }) {
  const sev = (k.severity ?? "probe").toLowerCase();
  return (
    <Card className={`p-4 ${sev === "fatal" ? "border-red-900/50" : ""}`}>
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm font-medium leading-snug text-zinc-200">{k.question}</p>
        <span className={`shrink-0 rounded border px-1.5 py-0.5 text-[10px] uppercase tracking-wider ${SEV_TONE[sev] ?? SEV_TONE.probe}`}>
          {sev}
        </span>
      </div>
      <p className="mt-2 text-xs leading-relaxed text-zinc-500">
        <span className="text-zinc-400">why it kills: </span>
        {k.why_fatal}
      </p>
      <p className="mt-1 text-xs text-zinc-600">triggered by: {k.triggered_by}</p>
      <p className="mt-2 rounded border border-emerald-900/40 bg-emerald-950/15 px-2 py-1.5 text-xs leading-relaxed text-emerald-300/80">
        <span className="uppercase tracking-wider text-emerald-600">what survives: </span>
        {k.passing_answer}
      </p>
    </Card>
  );
}

export default function AdversaryTab({ data }: { data: AdversaryData }) {
  return (
    <div className="space-y-4">
      <Card className="p-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="text-sm text-zinc-300">{data.overall_verdict}</p>
          <div className="flex gap-2">
            <span className="rounded border border-red-800/60 bg-red-950/30 px-2 py-0.5 text-xs text-red-400">
              {data.fatal_count ?? 0} fatal
            </span>
            <Badge tone="amber">{data.serious_count ?? 0} serious</Badge>
          </div>
        </div>
        <p className="mt-2 text-xs text-zinc-600">
          Three personas with real veto power cross-examined the decoded brief using its own sections as evidence.
          Anything marked fatal ends the company in a real hearing — answer it or cut it.
        </p>
      </Card>

      {data.ai_insight && <LLMInsight text={data.ai_insight} />}

      {(data.personas ?? []).map((p) => (
        <div key={p.persona} className="space-y-2">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <h4 className="text-sm font-semibold text-zinc-100">{p.role}</h4>
            <span className="text-[11px] text-zinc-600">{p.stance}</span>
          </div>
          <p className="text-xs text-zinc-500">{p.verdict}</p>
          {(p.kills ?? []).map((k, i) => (
            <Challenge key={i} k={k} />
          ))}
        </div>
      ))}

      <div>
        <h4 className="mb-2 text-xs uppercase tracking-wider text-zinc-500">Cross-examination protocol</h4>
        <Bullets items={data.protocol ?? []} />
      </div>
    </div>
  );
}
