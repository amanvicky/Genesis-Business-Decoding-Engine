"use client";

import { useEffect, useRef } from "react";
import { TABS, type AgentState, type ConsoleEvent, type LogLevel } from "@/lib/types";

const LEVEL_STYLE: Record<LogLevel, string> = {
  info: "text-zinc-400",
  warn: "text-amber-400",
  error: "text-red-400",
  success: "text-emerald-400",
  agent: "text-cyan-400",
};

interface ConsoleLine {
  time: string;
  agent: string;
  level: LogLevel;
  msg: string;
}

function toLines(events: readonly ConsoleEvent[]): ConsoleLine[] {
  const out: ConsoleLine[] = [];
  for (const ev of events) {
    if (ev.type === "log") {
      out.push({ time: new Date().toLocaleTimeString(), agent: ev.agent, level: ev.level, msg: ev.msg });
    } else if (ev.type === "status") {
      const mark = ev.state === "done" ? "✓" : ev.state === "failed" ? "✗" : "▸";
      const ms = ev.ms !== undefined ? ` (${ev.ms}ms)` : "";
      out.push({
        time: new Date().toLocaleTimeString(),
        agent: ev.agent,
        level: ev.state === "failed" ? "error" : ev.state === "done" ? "success" : "agent",
        msg: `${mark} ${ev.title}${ms}`,
      });
    } else if (ev.type === "section") {
      out.push({ time: new Date().toLocaleTimeString(), agent: ev.section.id, level: "success", msg: `section ready — Tab ${ev.section.id}` });
    } else if (ev.type === "error") {
      out.push({ time: new Date().toLocaleTimeString(), agent: "genesis", level: "error", msg: ev.msg });
    }
  }
  return out.slice(-400);
}

export default function AgentConsole({ events, running }: { events: readonly ConsoleEvent[]; running: boolean }) {
  const boxRef = useRef<HTMLDivElement>(null);
  const lines = toLines(events);

  useEffect(() => {
    boxRef.current?.scrollTo({ top: boxRef.current.scrollHeight });
  }, [events.length]);

  return (
    <div className="flex h-full flex-col overflow-hidden rounded-lg border border-edge bg-[#0b0b0e]">
      <div className="flex items-center justify-between border-b border-edge px-3 py-2">
        <span className="text-xs uppercase tracking-wider text-zinc-500">agent console</span>
        {running && (
          <span className="flex items-center gap-2 text-xs text-emerald-500">
            <span className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-emerald-500" /> live
          </span>
        )}
      </div>
      <div ref={boxRef} className="flex-1 overflow-y-auto p-3 font-mono text-xs leading-relaxed">
        {lines.length === 0 && !running && <p className="text-zinc-700">// console idle — run a decode to see intelligence gathering</p>}
        {lines.map((l, i) => (
          <div key={i} className="flex gap-2">
            <span className="shrink-0 text-zinc-700">{l.time}</span>
            <span className={`shrink-0 ${LEVEL_STYLE[l.level]}`}>[{l.agent}]</span>
            <span className={`${LEVEL_STYLE[l.level]} console-glow break-words`}>{l.msg}</span>
          </div>
        ))}
        {running && <span className="inline-block h-3.5 w-2 animate-pulse-dot bg-emerald-500/80" />}
      </div>
    </div>
  );
}

export function StatusRail({ status }: { status: Readonly<Record<string, AgentState>> }) {
  return (
    <div className="rounded-lg border border-edge bg-panel/60 p-3">
      <div className="mb-2 text-xs uppercase tracking-wider text-zinc-500">pipeline</div>
      <ol className="space-y-1">
        {TABS.map((t) => {
          const s = status[t.id];
          const glyph = s === "done" ? "✓" : s === "failed" ? "✗" : s === "running" ? "▸" : "·";
          const color =
            s === "done" ? "text-emerald-500" : s === "failed" ? "text-red-500" : s === "running" ? "text-cyan-400 animate-pulse-dot" : "text-zinc-700";
          return (
            <li key={t.id} className="flex items-center gap-2 text-xs">
              <span className={`w-3 ${color}`}>{glyph}</span>
              <span className={s ? "text-zinc-400" : "text-zinc-700"}>{t.title}</span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
