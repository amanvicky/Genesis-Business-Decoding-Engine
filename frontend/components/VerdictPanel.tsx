"use client";

import { useState } from "react";
import type { Report, VerdictMemo } from "@/lib/types";
import { requestVerdict } from "@/lib/api";
import { Badge } from "@/components/ui";

const DECISION_TONE: Record<string, string> = {
  GO: "green", "NO-GO": "red", CONDITIONAL: "amber", PENDING: "zinc",
};
const GATE_MARK: Record<string, string> = { pass: "✔", caution: "⚠", fail: "✘", pending: "…" };
const GATE_TONE: Record<string, string> = { pass: "green", caution: "amber", fail: "red", pending: "zinc" };

interface FmfQuestion {
  q: string;
  weight: string;
  invert?: boolean;
}

export default function VerdictPanel({ report, onClose }: { report: Report; onClose: () => void }) {
  const questions: FmfQuestion[] =
    (report.sections.marketsize?.data as unknown as { founder_market_fit?: { questions?: FmfQuestion[] } })
      ?.founder_market_fit?.questions ?? [];
  const [answers, setAnswers] = useState<(boolean | null)[]>(() => questions.map(() => null));
  const [memo, setMemo] = useState<VerdictMemo | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const answered = answers.filter((a) => a !== null).length;
  const canSubmit = answered === questions.length && questions.length > 0;

  const ask = async () => {
    setBusy(true);
    setErr(null);
    try {
      const m = await requestVerdict(report, answers.map((a) => a === true));
      setMemo(m);
    } catch {
      setErr("verdict failed — is the backend running?");
    } finally {
      setBusy(false);
    }
  };

  const download = () => {
    if (!memo) return;
    const md = [
      `# GENESIS VERDICT — ${memo.subject}`,
      `## Decision: ${memo.decision}`,
      "",
      memo.rationale,
      "",
      "## Gates",
      "",
      ...memo.gates.map((g) => `- [${g.status}] ${g.name} — ${g.basis}${g.fix ? `\n  - fix: ${g.fix}` : ""}`),
      "",
      `## FMF: ${memo.founder_market_fit.score}/${memo.founder_market_fit.total}`,
      "",
      ...memo.founder_market_fit.rows.map((r) => `- ${r.answer === null ? "—" : r.good ? "✔" : "✘"} (${r.weight}) ${r.q}`),
      "",
      "## Conditions",
      "",
      ...memo.conditions.map((c) => `- ${c}`),
      "",
      "## Next Actions",
      "",
      ...memo.next_actions.map((a) => `- ${a}`),
    ].join("\n");
    const blob = new Blob([md], { type: "text/markdown" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `GENESIS_VERDICT_${(memo.subject || "idea").replace(/[^\w-]+/g, "_").slice(0, 40)}.md`;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  const tone = (memo ? DECISION_TONE[memo.decision] ?? "zinc" : "zinc") as "green" | "red" | "amber" | "zinc";

  return (
    <div className="fixed inset-y-0 right-0 z-50 flex w-full max-w-md flex-col border-l border-edge bg-panel shadow-2xl">
      <div className="flex items-center justify-between border-b border-edge px-4 py-3">
        <div>
          <p className="text-sm font-semibold text-amber-400">⚖ Verdict Protocol</p>
          <p className="text-[11px] text-zinc-600">deterministic gates + your honest answers = the decision</p>
        </div>
        <button onClick={onClose} className="text-zinc-500 transition-colors hover:text-zinc-300" aria-label="Close verdict">✕</button>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto px-4 py-4">
        {questions.length > 0 ? (
          <div className="space-y-2">
            <p className="text-xs uppercase tracking-wider text-zinc-500">
              founder-market fit — answer honestly ({answered}/{questions.length})
            </p>
            {questions.map((q, i) => (
              <div key={i} className="rounded-lg border border-edge bg-panel/60 p-2.5">
                <p className="text-xs leading-relaxed text-zinc-300">
                  <span className="mr-1.5 font-mono text-[10px] uppercase text-zinc-600">{q.weight}</span>
                  {q.q}
                </p>
                <div className="mt-1.5 flex gap-1.5">
                  {[true, false].map((v) => (
                    <button key={String(v)} onClick={() => setAnswers((a) => a.map((x, j) => (j === i ? v : x)))}
                      className={`rounded border px-2.5 py-1 text-[11px] transition-colors ${
                        answers[i] === v
                          ? v ? "border-emerald-700 bg-emerald-950/40 text-emerald-400" : "border-red-800 bg-red-950/30 text-red-400"
                          : "border-edge text-zinc-500 hover:border-zinc-600"
                      }`}>
                      {v ? "yes" : "no"}
                    </button>
                  ))}
                </div>
              </div>
            ))}
            <button onClick={ask} disabled={!canSubmit || busy}
              className="w-full rounded-lg border border-emerald-800/70 bg-emerald-950/30 py-2 text-sm font-medium text-emerald-400 transition-colors hover:bg-emerald-900/30 disabled:opacity-40">
              {busy ? "computing verdict…" : canSubmit ? "Compute verdict" : "Answer all questions first"}
            </button>
          </div>
        ) : (
          <button onClick={ask} disabled={busy}
            className="w-full rounded-lg border border-emerald-800/70 bg-emerald-950/30 py-2 text-sm font-medium text-emerald-400 hover:bg-emerald-900/30 disabled:opacity-40">
            {busy ? "computing verdict…" : "Compute verdict from gates"}
          </button>
        )}

        {err && <p className="text-xs text-red-400">{err}</p>}

        {memo && (
          <div className="space-y-3">
            <div className="rounded-lg border border-emerald-900/50 bg-emerald-950/10 p-3">
              <div className="flex items-center justify-between">
                <p className="text-xs uppercase tracking-wider text-zinc-500">decision</p>
                <Badge tone={tone}>{memo.decision}</Badge>
              </div>
              <p className="mt-2 text-xs leading-relaxed text-zinc-300">{memo.rationale}</p>
            </div>

            <div className="space-y-1.5">
              {memo.gates.map((g) => (
                <div key={g.name} className="rounded border border-edge p-2">
                  <div className="flex items-center gap-2">
                    <Badge tone={(GATE_TONE[g.status] ?? "zinc") as "green" | "red" | "amber" | "zinc"}>{GATE_MARK[g.status]} {g.name}</Badge>
                  </div>
                  <p className="mt-1 text-[11px] leading-relaxed text-zinc-500">{g.basis}</p>
                  {g.fix && <p className="mt-0.5 text-[11px] leading-relaxed text-emerald-400/80">fix: {g.fix}</p>}
                </div>
              ))}
            </div>

            {memo.conditions.length > 0 && (
              <div>
                <p className="text-xs uppercase tracking-wider text-zinc-500">conditions</p>
                <ul className="mt-1 space-y-1">
                  {memo.conditions.map((c, i) => <li key={i} className="text-xs text-zinc-400">• {c}</li>)}
                </ul>
              </div>
            )}
            {memo.next_actions.length > 0 && (
              <div>
                <p className="text-xs uppercase tracking-wider text-zinc-500">next actions</p>
                <ul className="mt-1 space-y-1">
                  {memo.next_actions.map((a, i) => <li key={i} className="text-xs text-zinc-300">• {a}</li>)}
                </ul>
              </div>
            )}
            <button onClick={download}
              className="w-full rounded border border-edge py-1.5 text-xs text-zinc-400 transition-colors hover:border-emerald-700 hover:text-emerald-400">
              ↓ Verdict memo (.md)
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
