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

export default function VerdictPanel({ report, onClose }: { report: Report; onClose: () => void }) {
  const [memo, setMemo] = useState<VerdictMemo | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const ask = async () => {
    setBusy(true);
    setErr(null);
    try {
      const m = await requestVerdict(report, []);
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
          <p className="text-[11px] text-zinc-600">deterministic gates over the evidence = the decision</p>
        </div>
        <button onClick={onClose} className="text-zinc-500 transition-colors hover:text-zinc-300" aria-label="Close verdict">✕</button>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto px-4 py-4">
        <button onClick={ask} disabled={busy}
          className="w-full rounded-lg border border-emerald-800/70 bg-emerald-950/30 py-2 text-sm font-medium text-emerald-400 hover:bg-emerald-900/30 disabled:opacity-40">
          {busy ? "computing verdict…" : "Compute verdict from the evidence"}
        </button>

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
              Verdict memo (.md)
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
