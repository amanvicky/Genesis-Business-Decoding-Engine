"use client";

import type { MarketPerfData } from "@/lib/types";
import { Badge, Card, Warn } from "@/components/ui";
import { LLMInsight, Section } from "./AnalysisTabs";

function Sparkline({ closes, best, worst }: { closes: readonly number[]; best: number; worst: number }) {
  if (closes.length < 2) return null;
  const w = 720, h = 140, pad = 6;
  const min = Math.min(...closes), max = Math.max(...closes);
  const span = max - min || 1;
  const x = (i: number) => pad + (i / (closes.length - 1)) * (w - pad * 2);
  const y = (v: number) => h - pad - ((v - min) / span) * (h - pad * 2);
  const points = closes.map((c, i) => `${x(i).toFixed(1)},${y(c).toFixed(1)}`).join(" ");
  const bestIdx = closes.indexOf(best);
  const worstIdx = closes.indexOf(worst);
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full" role="img" aria-label="1-year price chart">
      <polyline points={points} fill="none" stroke="rgb(16,185,129)" strokeWidth="2" />
      {bestIdx >= 0 && <circle cx={x(bestIdx)} cy={y(closes[bestIdx]!)} r="4" fill="rgb(16,185,129)" />}
      {worstIdx >= 0 && <circle cx={x(worstIdx)} cy={y(closes[worstIdx]!)} r="4" fill="rgb(239,68,68)" />}
    </svg>
  );
}

export function MarketPerfTab({ data }: { data: MarketPerfData }) {
  const perf = data.performance;
  const cur = data.currency_display === "INR" ? "₹" : "$";
  const rises = perf?.best_weeks ?? [];
  const falls = perf?.worst_weeks ?? [];
  const spark = data.sparkline ?? [];
  const bestClose = spark.length ? Math.max(...spark) : 0;
  const worstClose = spark.length ? Math.min(...spark) : 0;
  const up = (perf?.change_1y_pct ?? 0) >= 0;

  return (
    <div className="space-y-4">
      <Card className="p-4">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="cyan">{data.traded ? (data.symbol ?? "listed") : (data.index?.name ?? "index")}</Badge>
          {data.traded === false && <Badge tone="amber">not publicly traded — index context</Badge>}
          {data.traded === null && <Badge>market data unavailable</Badge>}
        </div>
        {data.summary && <p className="mt-2 text-sm leading-relaxed text-zinc-200">{data.summary}</p>}
      </Card>

      {data.ai_insight && <LLMInsight text={data.ai_insight} />}

      {perf && spark.length > 1 && (
        <Section title={`1-year weekly closes (green dot = biggest rise, red = biggest fall)`}>
          <Sparkline closes={spark} best={bestClose} worst={worstClose} />
          <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-zinc-400 md:grid-cols-4">
            <p>1y: <span className={up ? "text-emerald-400" : "text-red-400"}>{perf.change_1y_pct! > 0 ? "+" : ""}{perf.change_1y_pct}%</span></p>
            <p>YTD: {perf.ytd_pct! > 0 ? "+" : ""}{perf.ytd_pct}%</p>
            <p>52w high: {cur}{perf.high_52w?.price?.toLocaleString()} ({perf.high_52w?.date})</p>
            <p>52w low: {cur}{perf.low_52w?.price?.toLocaleString()} ({perf.low_52w?.date})</p>
          </div>
        </Section>
      )}

      {perf && (rises.length > 0 || falls.length > 0) && (
        <Section title="Highlights — the rises and the falls">
          <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
            <div className="rounded-lg border border-emerald-900/50 bg-emerald-950/10 p-3">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-emerald-400">▲ biggest rises</p>
              <ul className="space-y-1.5">
                {rises.map((w) => (
                  <li key={w.date} className="text-xs text-zinc-300">
                    <span className="text-emerald-400">{w.change_pct > 0 ? "+" : ""}{w.change_pct}%</span> week of {w.date} — {cur}{w.from.toLocaleString()} → {cur}{w.to.toLocaleString()}
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-lg border border-red-900/50 bg-red-950/10 p-3">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-red-400">▼ biggest falls</p>
              <ul className="space-y-1.5">
                {falls.map((w) => (
                  <li key={w.date} className="text-xs text-zinc-300">
                    <span className="text-red-400">{w.change_pct}%</span> week of {w.date} — {cur}{w.from.toLocaleString()} → {cur}{w.to.toLocaleString()}
                  </li>
                ))}
              </ul>
            </div>
          </div>
          {perf.max_drawdown && (
            <p className="mt-3 text-xs text-zinc-500">
              worst drawdown: <span className="text-red-400">{perf.max_drawdown.pct}%</span> (as of {perf.max_drawdown.date}) — the deepest fall from a peak within the year.
            </p>
          )}
        </Section>
      )}

      {data.note && <Warn>{data.note}</Warn>}
    </div>
  );
}
