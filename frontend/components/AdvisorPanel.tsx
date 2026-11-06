"use client";

import { useRef, useState } from "react";
import type { AdviceEvent, Report, TabId } from "@/lib/types";
import { streamAdvice } from "@/lib/api";
import { Badge } from "@/components/ui";

interface Msg {
  role: "user" | "genesis";
  text: string;
  bullets?: readonly string[];
  openTabs?: readonly TabId[];
  followups?: readonly string[];
  err?: boolean;
}

const SEED: readonly Msg[] = [
  {
    role: "genesis",
    text: "Ask me anything in this dossier — capital, competitors, build order, risks. I answer from YOUR numbers.",
    followups: ["Should I raise or bootstrap?", "What do I build first?", "Who already does this?", "What's my biggest risk?"],
  },
];

export default function AdvisorPanel({ report, onClose, onOpenTab }: {
  report: Report;
  onClose: () => void;
  onOpenTab: (id: TabId) => void;
}) {
  const [msgs, setMsgs] = useState<readonly Msg[]>(SEED);
  const [trail, setTrail] = useState<string>("");
  const [busy, setBusy] = useState(false);
  const [input, setInput] = useState("");
  const abortRef = useRef<AbortController | null>(null);

  const ask = async (question: string) => {
    const q = question.trim();
    if (!q || busy) return;
    setInput("");
    setMsgs((m) => [...m, { role: "user", text: q }]);
    setBusy(true);
    setTrail("reading your dossier…");
    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    try {
      await streamAdvice(q, report, (ev: AdviceEvent) => {
        if (ev.type === "log") {
          setTrail(ev.msg || "");
        } else if (ev.type === "answer") {
          setTrail("");
          setMsgs((m) => [...m, {
            role: "genesis",
            text: ev.answer || "",
            bullets: ev.bullets,
            openTabs: ev.open_tabs,
            followups: ev.followups,
          }]);
        } else if (ev.type === "error") {
          setTrail("");
          setMsgs((m) => [...m, { role: "genesis", text: ev.msg || "advisor error", err: true }]);
        }
      }, ctrl.signal);
    } catch (e) {
      setTrail("");
      setMsgs((m) => [...m, { role: "genesis", text: "connection lost — is the backend up?", err: true }]);
    } finally {
      setBusy(false);
      setTrail("");
    }
  };

  return (
    <div className="fixed inset-y-0 right-0 z-50 flex w-full max-w-md flex-col border-l border-edge bg-panel shadow-2xl">
      <div className="flex items-center justify-between border-b border-edge px-4 py-3">
        <div>
          <p className="text-sm font-semibold text-emerald-400">◈ Ask Genesis</p>
          <p className="text-[11px] text-zinc-600">real-time answers from your dossier — no generic advice</p>
        </div>
        <button onClick={onClose} className="text-zinc-500 transition-colors hover:text-zinc-300" aria-label="Close advisor">✕</button>
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
        {msgs.map((m, i) => (
          <div key={i} className={m.role === "user" ? "text-right" : ""}>
            <div className={
              m.role === "user"
                ? "inline-block rounded-lg border border-edge bg-panel/60 px-3 py-2 text-left text-sm text-zinc-200"
                : `inline-block max-w-full rounded-lg border px-3 py-2 text-left text-sm ${m.err ? "border-red-900/60 bg-red-950/20 text-red-300" : "border-emerald-900/50 bg-emerald-950/10 text-zinc-200"}`
            }>
              <p className="whitespace-pre-wrap leading-relaxed">{m.text}</p>
              {(m.bullets?.length ?? 0) > 0 && (
                <ul className="mt-2 space-y-1">
                  {m.bullets!.map((b, j) => (
                    <li key={j} className="text-xs leading-relaxed text-zinc-400">
                      <span className="text-emerald-600">•</span> {b}
                    </li>
                  ))}
                </ul>
              )}
              {(m.openTabs?.length ?? 0) > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {m.openTabs!.map((t) => (
                    <button key={t} onClick={() => onOpenTab(t)} className="rounded border border-cyan-900/60 px-1.5 py-0.5 text-[10px] text-cyan-400 hover:bg-cyan-950/30">
                      open {t}
                    </button>
                  ))}
                </div>
              )}
            </div>
            {(m.followups?.length ?? 0) > 0 && (
              <div className="mt-2 flex flex-wrap gap-1.5">
                {m.followups!.map((f) => (
                  <button key={f} onClick={() => ask(f)} disabled={busy}
                    className="rounded-full border border-edge px-2.5 py-1 text-[11px] text-zinc-400 transition-colors hover:border-emerald-800 hover:text-emerald-400 disabled:opacity-40">
                    {f}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
        {busy && (
          <p className="flex items-center gap-2 text-xs text-cyan-400/80">
            <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-cyan-400" />
            {trail || "thinking…"}
          </p>
        )}
      </div>

      <form
        onSubmit={(e) => { e.preventDefault(); ask(input); }}
        className="flex gap-2 border-t border-edge p-3"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="e.g. Should I raise now? What do I build first?"
          maxLength={500}
          className="flex-1 rounded-lg border border-edge bg-panel/60 px-3 py-2 text-sm text-zinc-200 placeholder-zinc-600 outline-none focus:border-emerald-800/70"
        />
        <button type="submit" disabled={busy || !input.trim()}
          className="rounded-lg border border-emerald-800/70 bg-emerald-950/30 px-3 text-sm text-emerald-400 transition-colors hover:bg-emerald-900/30 disabled:opacity-40">
          Ask
        </button>
      </form>
    </div>
  );
}
