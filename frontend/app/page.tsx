"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  ackWatchDrifts,
  fetchHealth,
  fetchWatchStatus,
  markWatched,
  streamAnalysis,
  streamBattle,
  triggerWatchCheck,
  type HealthInfo,
} from "@/lib/api";
import {
  TABS,
  TAB_IDS,
  type AnalyzeRequest,
  type BattleResult,
  type ConsoleEvent,
  type LogLevel,
  type Report,
  type TabId,
  type WatchStatus,
} from "@/lib/types";
import AgentConsole, { StatusRail } from "@/components/AgentConsole";
import BattleMatrix from "@/components/BattleMatrix";
import InputPanel from "@/components/InputPanel";
import ReportViewer from "@/components/ReportViewer";
import WatchDrifts from "@/components/WatchDrifts";
import { CodeBlock } from "@/components/ui";

type RunPhase =
  | { phase: "idle" }
  | { phase: "running" }
  | { phase: "done" }
  | { phase: "error"; msg: string };

const REPO = "https://github.com/amanvicky/Genesis-Business-Decoding-Engine";

const SOURCES: readonly { name: string; gives: string }[] = [
  { name: "The company's own site", gives: "features, pricing language, legal identity" },
  { name: "Surface search", gives: "pain and alternatives" },
  { name: "Wikipedia", gives: "the founding story" },
  { name: "GitHub releases", gives: "shipped features, dated" },
  { name: "Hacker News", gives: "operator sentiment" },
  { name: "Reddit", gives: "user complaints" },
  { name: "Wayback Machine", gives: "pricing history" },
  { name: "SEC EDGAR", gives: "revenue history, registration fields" },
  { name: "Domain registries (RDAP)", gives: "the domain's own registration record" },
  { name: "LinkedIn & Medium", gives: "professional posts, essays" },
  { name: "GDELT global press", gives: "magazine coverage worldwide" },
  { name: "Have I Been Pwned", gives: "breach exposure" },
  { name: "Ahmia (Tor)", gives: "lawful OSINT" },
];

const AGENT_JOBS: readonly [string, string][] = [
  ["structural", "pain, moats, score"],
  ["features", "build vs bloat"],
  ["compliance", "blockers, costed"],
  ["premortem", "matched deaths"],
  ["timeline", "pivots or gates"],
  ["pricing", "LTV:CAC sandbox"],
  ["friction", "user complaints"],
  ["financial", "burn, runway, breakeven"],
  ["distribution", "first-ten plan"],
  ["techarch", "starter code"],
  ["darkweb", "breach shield"],
  ["playbook", "phased execution"],
  ["marketsize", "raise vs bootstrap"],
  ["dna", "feature philosophy"],
  ["school", "the curriculum"],
  ["markets", "stock rises and falls"],
  ["deepdive", "the company, feature by feature"],
  ["publicrecord", "registration & registry IDs"],
  ["adversary", "cross-examined"],
];

const PREVIEW_LINES: readonly { agent: string; level: LogLevel; msg: string }[] = [
  { agent: "recon", level: "success", msg: "official site locked: notion.com" },
  { agent: "features", level: "info", msg: "decompiling feature history…" },
  { agent: "dna", level: "success", msg: "✓ Product DNA (17ms)" },
  { agent: "deepdive", level: "success", msg: "✓ Company Deep-Dive (655ms)" },
  { agent: "genesis", level: "success", msg: "decode complete: 19/19 sections, 55 sources cited" },
];

const PREVIEW_LEVEL: Record<LogLevel, string> = {
  info: "text-zinc-400",
  warn: "text-amber-400",
  error: "text-red-400",
  success: "text-amber-400",
  agent: "text-cyan-400",
};

const CAPTURED: readonly { id: TabId; file: string; label: string }[] = [
  { id: "deepdive", file: "/captures/tab_deepdive.png", label: "Deep-dive" },
  { id: "structural", file: "/captures/tab_structural.png", label: "Structural" },
  { id: "marketsize", file: "/captures/tab_marketsize.png", label: "Market sizing" },
  { id: "dna", file: "/captures/tab_dna.png", label: "Product DNA" },
  { id: "markets", file: "/captures/tab_markets.png", label: "Stock performance" },
  { id: "compliance", file: "/captures/tab_compliance.png", label: "Compliance" },
];

export default function Page() {
  const [health, setHealth] = useState<HealthInfo | null>(null);
  const [phase, setPhase] = useState<RunPhase>({ phase: "idle" });
  const [events, setEvents] = useState<readonly ConsoleEvent[]>([]);
  const [report, setReport] = useState<Report | null>(null);
  const [arrived, setArrived] = useState<readonly TabId[]>([]);
  const [status, setStatus] = useState<Readonly<Record<string, "running" | "done" | "failed">>>({});
  const [battle, setBattle] = useState<BattleResult | null>(null);
  const [battlePlan, setBattlePlan] = useState<string[]>([]);
  const [battleIdx, setBattleIdx] = useState(0);
  const [briefId, setBriefId] = useState<string | null>(null);
  const [watched, setWatched] = useState(false);
  const [watchStatus, setWatchStatus] = useState<WatchStatus | null>(null);
  const [watchOpen, setWatchOpen] = useState(false);
  const [shot, setShot] = useState(0);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    fetchHealth().then(setHealth);
  }, []);

  // Reality Watch: this open IS the lazy trigger — anything due re-decodes in
  // the background while the dashboard is open; the chip shows the outcome.
  const refreshWatch = useCallback(async () => {
    const s = await fetchWatchStatus();
    if (s) setWatchStatus(s);
  }, []);
  useEffect(() => {
    triggerWatchCheck();
    refreshWatch();
    const t = setInterval(refreshWatch, 45_000);
    return () => clearInterval(t);
  }, [refreshWatch]);

  const reset = useCallback(() => {
    abortRef.current?.abort(); // a re-run/reset must sever any in-flight stream
    abortRef.current = null;
    setPhase({ phase: "idle" });
    setEvents([]);
    setReport(null);
    setArrived([]);
    setStatus({});
    setBattle(null);
    setBattlePlan([]);
    setBattleIdx(0);
    setBriefId(null);
    setWatched(false);
  }, []);

  const run = useCallback((req: AnalyzeRequest) => {
    abortRef.current?.abort(); // clicking RUN twice must not interleave two streams
    const ac = new AbortController();
    abortRef.current = ac;

    setEvents([]);
    setReport(null);
    setArrived([]);
    setStatus({});
    setBattle(null);
    setBriefId(null);
    setWatched(false);
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
        case "saved":
          setBriefId(ev.brief_id);
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

  const runBattle = useCallback((req: { ideas: string[]; geography: "india" | "us" | "global"; context?: string; team_size: number; runway_target_months: number; include_darkweb: boolean }) => {
    abortRef.current?.abort();
    const ac = new AbortController();
    abortRef.current = ac;

    setEvents([]);
    setReport(null);
    setArrived([]);
    setStatus({});
    setBattle(null);
    setBriefId(null);
    setWatched(false);
    setBattlePlan(req.ideas);
    setBattleIdx(0);
    setPhase({ phase: "running" });

    const stale = () => abortRef.current !== ac;
    streamBattle(req, (ev) => {
      if (stale()) return;
      if (ev.type === "battle_start") return;
      if (ev.type === "idea_start") {
        setBattleIdx(ev.i);
        return;
      }
      if (ev.type === "idea_done") {
        setBattleIdx(ev.i + 1); // the placeholder then points at the NEXT idea
        return;
      }
      if (ev.type === "battle_done") {
        setBattle({ rows: ev.rows, winner: ev.winner, prose: ev.prose, llm_wrote_prose: ev.llm_wrote_prose });
        setPhase({ phase: "done" });
        refreshWatch();
        return;
      }
      if (ev.type === "error") {
        setPhase({ phase: "error", msg: ev.msg });
        return;
      }
      // logs and agent status feed the same console as a normal decode
      setEvents((prev) => [...prev, ev]);
      if (ev.type === "status") setStatus((prev) => ({ ...prev, [ev.agent]: ev.state }));
    }, ac.signal).catch((err: unknown) => {
      if (stale() || (err instanceof DOMException && err.name === "AbortError")) return;
      setPhase({ phase: "error", msg: err instanceof Error ? err.message : String(err) });
    });
  }, [refreshWatch]);

  const watchThis = useCallback(async () => {
    if (!briefId) return;
    if (await markWatched(briefId, 7)) {
      setWatched(true);
      refreshWatch();
    }
  }, [briefId, refreshWatch]);

  const ackDrifts = useCallback(async () => {
    if (await ackWatchDrifts()) refreshWatch();
  }, [refreshWatch]);

  const running = phase.phase === "running";
  const hasReport = report !== null && arrived.length > 0;
  const capture = CAPTURED[shot] ?? CAPTURED[0]!;
  const unseenDriftCount = watchStatus?.drifts?.filter((d) => !d.seen).length ?? 0;
  const canWatch = phase.phase === "done" && briefId !== null && !battle && report?.request.mode !== "idea";

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-[1440px] flex-col px-4 pb-8 md:px-8">
      {/* Header */}
      <header className="flex h-16 items-center justify-between border-b border-edge">
        <a href="/" aria-label="Genesis home" className="flex items-baseline gap-3">
          <span className="font-display text-lg font-bold tracking-tight text-zinc-100">◈ Genesis</span>
          <span className="hidden text-xs text-zinc-500 sm:inline">the zero-cost business decoding engine</span>
        </a>
        <a href={REPO} target="_blank" rel="noreferrer" className="border border-edge px-3 py-1.5 text-xs text-zinc-300 transition-colors duration-150 hover:border-amber-700 hover:text-amber-400">
          GitHub
        </a>
      </header>

      {/* Reality Watch strip — the drift chip lives here, visible on every screen */}
      {watchStatus && (watchStatus.running || (watchStatus.drifts?.length ?? 0) > 0) && (
        <div className="border-b border-edge bg-paper-2 px-4 py-2">
          <button
            onClick={() => setWatchOpen((v) => !v)}
            className="flex w-full items-center gap-2 text-left text-xs"
          >
            <span className={`inline-flex items-center gap-1.5 border px-2 py-1 ${watchStatus.running ? "border-cyan-900/60 text-cyan-400" : unseenDriftCount > 0 ? "border-amber-700 text-amber-400" : "border-edge text-zinc-500"}`}>
              <span className={`h-1.5 w-1.5 ${watchStatus.running ? "animate-pulse bg-cyan-400" : unseenDriftCount > 0 ? "bg-amber-400" : "bg-zinc-600"}`} aria-hidden="true" />
              {watchStatus.running
                ? `watch: re-checking ${watchStatus.done}/${watchStatus.total}${watchStatus.current ? ` — ${watchStatus.current}` : ""}`
                : `watch: ${unseenDriftCount > 0 ? `${unseenDriftCount} drift${unseenDriftCount === 1 ? "" : "s"}` : `${watchStatus.drifts.length} drift alert(s), read`} · ${watchStatus.watched_count} watched`}
            </span>
            <span className="text-zinc-600">{watchOpen ? "▾" : "▸"}</span>
          </button>
          {watchOpen && (
            <div className="mt-2 max-w-2xl">
              <WatchDrifts status={watchStatus} onAck={ackDrifts} />
            </div>
          )}
        </div>
      )}

      {/* Idle: the instrument */}
      {phase.phase === "idle" && (
        <main>
          <section className="grid min-h-[calc(100svh-4rem)] grid-cols-1 items-start gap-10 py-10 lg:grid-cols-12">
            <div className="lg:col-span-7">
              <h1 className="font-display text-[clamp(2.5rem,4.5vw,4.25rem)] font-bold leading-[1.04] tracking-[-0.02em] text-zinc-100">
                Read any company<br className="sm:hidden" /> in full.
              </h1>
              <p className="mt-4 max-w-[34ch] text-lg text-zinc-400">
                Nineteen free agents decode a business — by name, by website URL, or from a raw idea — into a
                nineteen-tab intelligence brief. Battle two ideas, then watch the winner for drift.
              </p>
              <div className="mt-8 max-w-2xl">
                <InputPanel running={running} onRun={run} onBattle={runBattle} />
              </div>
            </div>
            <div className="lg:col-span-5">
              <div className="flex h-[440px] flex-col border border-edge bg-paper-2 lg:h-[clamp(640px,calc(100svh-11rem),820px)]">
                <div className="flex items-center justify-between border-b border-edge px-3 py-2">
                  <span className="text-xs text-zinc-500">the Notion decode</span>
                  <span className="text-xs text-zinc-600">complete</span>
                </div>
                <div className="space-y-1.5 p-3 pb-0 font-mono text-xs leading-relaxed">
                  {PREVIEW_LINES.map((l, i) => (
                    <div key={i} className="console-line flex gap-2" style={{ "--i": i } as React.CSSProperties}>
                      <span className={`shrink-0 ${PREVIEW_LEVEL[l.level]}`}>[{l.agent}]</span>
                      <span className="text-zinc-400">{l.msg}</span>
                    </div>
                  ))}
                  <span className="mt-1 inline-block h-3.5 w-2 bg-amber-400/80" aria-hidden="true" />
                </div>
                <div className="min-h-0 flex-1 p-3 pt-3">
                  <img
                    src="/captures/report_deepdive.png"
                    alt="The brief this decode produced: the company deep-dive tab"
                    width={2880}
                    height={1800}
                    className="h-[280px] w-full border border-edge object-cover object-left-top sm:h-[320px] lg:h-full lg:object-top"
                  />
                </div>
              </div>
            </div>
          </section>

          {/* The brief: real captures */}
          <section className="border-t border-edge py-16">
            <h2 className="font-display text-[clamp(2rem,2.5vw+1rem,3.5rem)] font-bold leading-[1.05] tracking-[-0.02em] text-zinc-100">
              The brief, tab by tab.
            </h2>
            <p className="mt-2 max-w-[52ch] text-sm text-zinc-400">
              Captures of a live decode of Notion. Six of the nineteen tabs; the rest render the same way.
            </p>
            <div className="mt-6 flex gap-1 overflow-x-auto pb-1" role="tablist" aria-label="brief tab captures">
              {CAPTURED.map((c, i) => {
                const tab = TABS.find((t) => t.id === c.id);
                return (
                  <button
                    key={c.id}
                    role="tab"
                    aria-selected={i === shot}
                    onClick={() => setShot(i)}
                    className={`flex shrink-0 items-center gap-1.5 border px-3 py-2 text-xs transition-colors duration-150 ${
                      i === shot ? "border-amber-700 bg-amber-950/30 text-amber-400" : "border-edge text-zinc-400 hover:text-zinc-200"
                    }`}
                  >
                    <span aria-hidden="true">{tab?.icon}</span>
                    <span className="font-mono">{tab?.n}</span>
                    <span className="hidden md:inline">{c.label}</span>
                  </button>
                );
              })}
            </div>
            <figure className="mt-4" data-slot data-kind="product">
              <img
                src={capture.file}
                alt={`Genesis brief, ${capture.label} tab`}
                width={2880}
                height={1800}
                loading="lazy"
                className="w-full border border-edge"
              />
              <figcaption className="mt-2 text-xs text-zinc-500">
                {capture.label} tab of a live Notion decode
              </figcaption>
            </figure>
          </section>

          {/* The pipeline */}
          <section className="border-t border-edge pt-24 pb-24 mb-16">
            <h2 className="font-display text-[clamp(2rem,2.5vw+1rem,3.5rem)] font-bold leading-[1.05] tracking-[-0.02em] text-zinc-100">
              Nineteen agents, one pass.
            </h2>
            <ol className="mt-6 grid grid-cols-1 gap-x-10 gap-y-0 md:grid-cols-2">
              {AGENT_JOBS.map(([id, job], i) => (
                <li key={id} className="flex items-baseline gap-3 border-b border-edge/40 py-2 text-sm">
                  <span className="w-6 shrink-0 text-right font-mono text-xs text-zinc-600">{String(i + 1).padStart(2, "0")}</span>
                  <span className="w-24 shrink-0 font-mono text-xs text-amber-400/90">{id}</span>
                  <span className="text-zinc-400">{job}</span>
                </li>
              ))}
            </ol>
          </section>

          {/* What it reads */}
          <section className="border-t border-edge pt-24 pb-24 mb-16">
            <h2 className="font-display text-[clamp(2rem,2.5vw+1rem,3.5rem)] font-bold leading-[1.05] tracking-[-0.02em] text-zinc-100">
              Thirteen keyless sources.
            </h2>
            <dl className="mt-6 grid grid-cols-1 gap-x-10 gap-y-3 bg-paper-2 p-6 md:grid-cols-2 lg:p-8">
              {SOURCES.map((s) => (
                <div key={s.name} className="text-sm">
                  <dt className="text-zinc-200">{s.name}</dt>
                  <dd className="mt-0.5 text-zinc-400">{s.gives}</dd>
                </div>
              ))}
            </dl>
          </section>

          {/* Run it */}
          <section className="border-t border-edge py-16">
            <h2 className="font-display text-[clamp(2rem,2.5vw+1rem,3.5rem)] font-bold leading-[1.05] tracking-[-0.02em] text-zinc-100">
              One paste.
            </h2>
            <p className="mt-2 max-w-[52ch] text-sm text-zinc-400">
              Windows: paste this into PowerShell once — Genesis installs itself
              hidden and opens the dashboard. Nothing else touches your PC.
            </p>
            <div className="mt-6 max-w-2xl">
              <CodeBlock
                path="powershell"
                content={`irm https://raw.githubusercontent.com/amanvicky/Genesis-Business-Decoding-Engine/main/scripts/install_from_web.ps1 | iex`}
              />
            </div>
            <p className="mt-4 max-w-[52ch] text-xs text-zinc-600">
              or from source: git clone the repo, then python genesis.py up · or a
              classic Setup.exe from the Releases page · or the free cloud demo in deploy/
            </p>
            <div className="mt-8 grid grid-cols-1 gap-px bg-edge sm:grid-cols-3">
              <div className="bg-paper px-4 py-3">
                <p className="font-mono text-sm text-amber-400">port 3000</p>
                <p className="mt-1 text-xs text-zinc-400">the dashboard</p>
              </div>
              <div className="bg-paper px-4 py-3">
                <p className="font-mono text-sm text-amber-400">port 8000</p>
                <p className="mt-1 text-xs text-zinc-400">the API docs</p>
              </div>
              <div className="bg-paper px-4 py-3">
                <p className="font-mono text-sm text-amber-400">0 keys</p>
                <p className="mt-1 text-xs text-zinc-400">everything stays local</p>
              </div>
            </div>
          </section>
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
            {canWatch && (
              <button
                onClick={watchThis}
                disabled={watched}
                className={`border py-2 text-xs transition-colors duration-150 ${
                  watched
                    ? "border-emerald-900/60 text-emerald-500/90"
                    : "border-edge text-zinc-400 hover:border-amber-700 hover:text-amber-400"
                }`}
              >
                {watched ? "✓ watched — re-checks when the dashboard opens (every 7d)" : "watch this subject — re-decode it every 7 days and alert on drift"}
              </button>
            )}
            <button
              onClick={reset}
              className="border border-edge py-2 text-xs text-zinc-500 transition-colors duration-150 hover:border-zinc-600 hover:text-zinc-300"
            >
              New decode
            </button>
          </div>

          <div data-capture="report" className="min-h-0 lg:col-span-8 xl:col-span-9">
            {phase.phase === "error" ? (
              <div className="border border-red-900/50 bg-red-950/20 p-6">
                <p className="text-sm font-medium text-red-400">Pipeline error</p>
                <p className="mt-1 font-mono text-xs text-red-300/80">{phase.msg}</p>
                <p className="mt-3 text-xs text-zinc-500">
                  Is the backend running? Start it with <code className="text-zinc-400">uvicorn app.main:app</code> from
                  the backend directory.
                </p>
              </div>
            ) : battle ? (
              <BattleMatrix result={battle} />
            ) : hasReport ? (
              <ReportViewer report={report} streaming={running} arrivedIds={arrived} />
            ) : (
              <div className="flex h-full min-h-64 items-center justify-center border border-dashed border-edge">
                <p className="text-sm text-zinc-500">
                  {battlePlan.length > 0
                    ? `battle: decoding idea ${String.fromCharCode(65 + Math.min(battleIdx, battlePlan.length - 1))} of ${battlePlan.length} — each idea runs the full 19-agent pipeline, one at a time`
                    : "gathering intelligence: sections stream in as each agent finishes"}
                </p>
              </div>
            )}
          </div>
        </main>
      )}

      {/* Footer mast */}
      <footer className="mt-16 border-t border-edge pt-6">
        <div className="mb-3 flex flex-wrap items-center gap-2 text-[11px]">
          <Chip ok={!!health} label={health ? `API v${health.version}` : "API offline"} />
          {health?.offline_mode && <Chip ok={false} label="offline mode" />}
          <Chip ok={!!health?.llm.available} label={health?.llm.available ? `LLM: ${health.llm.model}` : "no local LLM"} />
          <Chip ok={!!health?.tor.available} label={health?.tor.available ? "Tor live" : "Tor off"} />
          <Chip ok={false} label={`vault: ${watchStatus?.watched_count ?? 0} watched brief(s)`} />
        </div>
        <div className="flex flex-wrap items-baseline justify-between gap-3">
          <span className="font-display text-sm font-bold tracking-tight text-zinc-200">◈ Genesis</span>
          <span className="text-xs text-zinc-600">{TAB_IDS.length}-agent pipeline, MIT licensed, runs on your machine.</span>
        </div>
        <p className="mt-2 max-w-[70ch] text-xs text-zinc-600">
          Planning-grade intelligence assembled from public sources. Not legal or financial advice.
        </p>
      </footer>
    </div>
  );
}

function Chip({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 border px-2 py-1 ${
        ok ? "border-emerald-900/60 text-emerald-500/90" : "border-edge text-zinc-600"
      }`}
    >
      <span className={`h-1.5 w-1.5 ${ok ? "bg-emerald-500" : "bg-zinc-700"}`} aria-hidden="true" />
      {label}
    </span>
  );
}
