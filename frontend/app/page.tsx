"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { fetchHealth, streamAnalysis, type HealthInfo } from "@/lib/api";
import {
  TAB_IDS,
  type AnalyzeRequest,
  type ConsoleEvent,
  type Report,
  type TabId,
} from "@/lib/types";
import AgentConsole, { StatusRail } from "@/components/AgentConsole";
import InputPanel from "@/components/InputPanel";
import ReportViewer from "@/components/ReportViewer";

type RunPhase =
  | { phase: "idle" }
  | { phase: "running" }
  | { phase: "done" }
  | { phase: "error"; msg: string };

export default function Page() {
  const [health, setHealth] = useState<HealthInfo | null>(null);
  const [phase, setPhase] = useState<RunPhase>({ phase: "idle" });
  const [events, setEvents] = useState<readonly ConsoleEvent[]>([]);
  const [report, setReport] = useState<Report | null>(null);
  const [arrived, setArrived] = useState<readonly TabId[]>([]);
  const [status, setStatus] = useState<Readonly<Record<string, "running" | "done" | "failed">>>({});
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    fetchHealth().then(setHealth);
  }, []);

  const reset = useCallback(() => {
    abortRef.current?.abort(); // a re-run/reset must sever any in-flight stream
    abortRef.current = null;
    setPhase({ phase: "idle" });
    setEvents([]);
    setReport(null);
    setArrived([]);
    setStatus({});
  }, []);

  const run = useCallback((req: AnalyzeRequest) => {
    abortRef.current?.abort(); // clicking RUN twice must not interleave two streams
    const ac = new AbortController();
    abortRef.current = ac;

    setEvents([]);
    setReport(null);
    setArrived([]);
    setStatus({});
    setPhase({ phase: "running" });

    const stale = () => abortRef.current !== ac;
    streamAnalysis(req, (ev) => {
      if (stale()) return;
      setEvents((prev) => [...prev, ev]);
      switch (ev.type) {
        case "status":
          setStatus((prev) => ({ ...prev, [ev.agent]: ev.state }));
          break;
        case "section":
          setArrived((prev) => (prev.includes(ev.section.id) ? prev : [...prev, ev.section.id]));
          break;
        case "done":
          setReport(ev.report);
          setPhase({ phase: "done" });
          break;
        case "error":
          setPhase({ phase: "error", msg: ev.msg });
          break;
        case "log":
          break;
        default: {
          const never: never = ev;
          void never;
        }
      }
    }, ac.signal).catch((err: unknown) => {
      if (stale() || (err instanceof DOMException && err.name === "AbortError")) return;
      setPhase({ phase: "error", msg: err instanceof Error ? err.message : String(err) });
    });
  }, []);

  const running = phase.phase === "running";
  const hasReport = report !== null && arrived.length > 0;

  return (
    <div className="mx-auto flex min-h-screen max-w-[1500px] flex-col px-4 pb-8">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-edge py-4">
        <div className="flex items-baseline gap-3">
          <span className="text-lg font-semibold tracking-[0.2em] text-zinc-100">◈ GENESIS</span>
          <span className="hidden text-xs text-zinc-600 sm:inline">The Zero-Cost Business Decoding &amp; Replication Engine</span>
        </div>
        <div className="flex items-center gap-2 text-[11px]">
          <Chip ok={!!health} label={health ? `API v${health.version}` : "API offline"} />
          {health?.offline_mode && <Chip ok={false} label="OFFLINE MODE" />}
          <Chip ok={!!health?.llm.available} label={health?.llm.available ? `LLM: ${health.llm.model}` : "no local LLM"} />
          <Chip ok={!!health?.tor.available} label={health?.tor.available ? "Tor live" : "Tor off"} />
        </div>
      </header>

      {/* Idle hero */}
      {phase.phase === "idle" && (
        <main className="flex flex-1 flex-col items-center justify-center py-16">
          <h1 className="max-w-2xl text-center text-2xl font-semibold leading-snug text-zinc-100">
            Absolute clarity on any company or idea.
            <span className="block text-zinc-500">Structure. Features. Compliance. Pricing. Friction. Failure modes. Execution.</span>
          </h1>
          <p className="mt-3 max-w-xl text-center text-sm text-zinc-600">
            Sixteen analysis agents scrape free public sources — surface web, Wikipedia, GitHub releases, HN, review
            platforms, Wayback pricing archives, and optionally Tor-routed OSINT — and assemble a 12-tab intelligence
            dossier. No accounts, no API keys, no cost.
          </p>
          <div className="mt-8 w-full">
            <InputPanel running={running} onRun={run} />
          </div>
        </main>
      )}

      {/* Running / done workspace */}
      {phase.phase !== "idle" && (
        <main className="mt-4 grid min-h-0 flex-1 grid-cols-1 gap-4 lg:grid-cols-12">
          <div className="flex min-h-0 flex-col gap-4 lg:col-span-4 xl:col-span-3">
            <div className="h-80 min-h-0 lg:h-[calc(100vh-190px)]">
              <AgentConsole events={events} running={running} />
            </div>
            <StatusRail status={status} />
            <button
              onClick={reset}
              className="rounded-lg border border-edge py-2 text-xs text-zinc-500 transition-colors hover:border-zinc-700 hover:text-zinc-300"
            >
              ← new decode
            </button>
          </div>

          <div className="min-h-0 lg:col-span-8 xl:col-span-9">
            {phase.phase === "error" ? (
              <div className="rounded-lg border border-red-900/50 bg-red-950/20 p-6">
                <p className="text-sm font-medium text-red-400">Pipeline error</p>
                <p className="mt-1 font-mono text-xs text-red-300/80">{phase.msg}</p>
                <p className="mt-3 text-xs text-zinc-500">
                  Is the backend running? Start it with <code className="text-zinc-400">uvicorn app.main:app</code> from
                  the backend directory.
                </p>
              </div>
            ) : hasReport ? (
              <ReportViewer report={report} streaming={running} arrivedIds={arrived} />
            ) : (
              <div className="flex h-full min-h-64 items-center justify-center rounded-lg border border-dashed border-edge">
                <p className="text-sm text-zinc-600">gathering intelligence… sections stream in as each agent finishes</p>
              </div>
            )}
          </div>
        </main>
      )}

      <footer className="mt-8 border-t border-edge pt-3 text-center text-[11px] text-zinc-700">
        100% local and free · MIT licensed · planning-grade intelligence from public sources — not legal or financial
        advice · {TAB_IDS.length}-agent pipeline
      </footer>
    </div>
  );
}

function Chip({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded border px-2 py-1 ${
        ok ? "border-emerald-900/60 text-emerald-500/90" : "border-edge text-zinc-600"
      }`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${ok ? "bg-emerald-500" : "bg-zinc-700"}`} />
      {label}
    </span>
  );
}
