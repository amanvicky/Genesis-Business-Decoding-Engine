"use client";

import { useMemo, useState } from "react";

import { Badge, Bullets, Card, Rows, Warn } from "@/components/ui";
import type { DnaData, FrictionData, PricingData, TimelineData } from "@/lib/types";
import { LLMInsight, Section } from "./AnalysisTabs";

export function TimelineTab({ data }: { data: TimelineData }) {
  if (data.mode === "idea") {
    return (
      <div className="space-y-4">
        {data.note && <Warn>{data.note}</Warn>}
        {data.ai_insight && <LLMInsight text={data.ai_insight} />}
        <div className="space-y-3">
          {(data.gates ?? []).map((g) => (
            <Card key={g.gate} className="p-4">
              <p className="text-sm font-medium text-emerald-400/90">{g.gate}</p>
              <p className="mt-1 text-xs leading-relaxed text-zinc-400">{g.exit_criteria}</p>
              <p className="mt-1 text-xs text-zinc-600">artifacts: {g.artifacts.join(", ")}</p>
            </Card>
          ))}
        </div>
      </div>
    );
  }
  return (
    <div className="space-y-4">
      {data.ai_insight && <LLMInsight text={data.ai_insight} />}
      <div className="relative space-y-3 border-l border-edge pl-4">
        {(data.events ?? []).map((e, i) => (
          <div key={i} className="relative">
            <span className={`absolute -left-[21px] top-1.5 h-2 w-2 rounded-full ${e.pivot ? "bg-amber-400" : "bg-zinc-600"}`} />
            <div className="flex items-baseline gap-2">
              <span className="font-mono text-xs text-emerald-500">{e.date ?? e.year}</span>
              {e.pivot && <Badge tone="amber">PIVOT</Badge>}
            </div>
            <p className="mt-0.5 text-sm leading-relaxed text-zinc-400">{e.event}</p>
          </div>
        ))}
      </div>
      {data.funding_events && data.funding_events.length > 0 && (
        <Section title="Funding events">
          <Rows
            rows={data.funding_events}
            cols={[
              { key: "amount", label: "Amount" },
              { key: "context", label: "Context" },
            ]}
          />
        </Section>
      )}
    </div>
  );
}

export function PricingTab({ data }: { data: PricingData }) {
  return (
    <div className="space-y-4">
      {data.ai_insight && <LLMInsight text={data.ai_insight} />}

      {(data.tiers ?? []).length > 0 && (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          {(data.tiers ?? []).map((t, i) => (
            <Card key={i} className="p-4">
              <p className="text-xs uppercase tracking-wider text-zinc-500">{t.name}</p>
              <p className="mt-1 font-mono text-lg text-emerald-400">{t.price}</p>
              {t.context && <p className="mt-1 line-clamp-3 text-[11px] text-zinc-600">{t.context}</p>}
            </Card>
          ))}
        </div>
      )}

      <Section title="Packaging psychology">
        <Rows
          rows={data.psychology ?? []}
          cols={[
            { key: "driver", label: "Driver" },
            { key: "evidence", label: "Evidence / mechanism" },
          ]}
        />
      </Section>

      {(data.history ?? []).length > 0 && (
        <Section title="Pricing archaeology (Wayback snapshots)">
          <div className="space-y-2">
            {(data.history ?? []).map((h) => (
              <Card key={h.date} className="p-3">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs text-emerald-500">{h.date}</span>
                  <a href={h.snapshot} target="_blank" rel="noreferrer" className="text-[11px] text-cyan-500/80 hover:text-cyan-400">
                    snapshot
                  </a>
                </div>
                <p className="mt-1 text-xs text-zinc-500">{h.prices.map((p) => p.raw).join(" · ")}</p>
              </Card>
            ))}
          </div>
        </Section>
      )}
    </div>
  );
}

export function FrictionTab({ data }: { data: FrictionData }) {
  return (
    <div className="space-y-4">
      <Card className="p-4">
        <p className="text-sm text-zinc-300">{data.voice_count ?? 0} public voices mined</p>
        {data.caveat && <p className="mt-1 text-xs text-zinc-600">{data.caveat}</p>}
      </Card>

      {data.ai_insight && <LLMInsight text={data.ai_insight} />}

      {(data.complaint_clusters ?? []).length > 0 && (
        <Section title="Complaint clusters">
          <div className="space-y-1.5">
            {(data.complaint_clusters ?? []).map((c) => (
              <div key={c.cluster}>
                <div className="flex justify-between text-xs">
                  <span className="text-zinc-300">{c.cluster}</span>
                  <span className="font-mono text-zinc-500">
                    {c.count} · {c.share}
                  </span>
                </div>
                <div className="mt-0.5 h-1.5 overflow-hidden rounded bg-zinc-900">
                  <div className="h-full rounded bg-red-500/50 transition-all duration-500" style={{ width: c.share }} />
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}

      <Section title="Representative voices (unvarnished)">
        <Rows
          rows={(data.representative_voices ?? [])}
          cols={[
            { key: "source", label: "Source" },
            { key: "cluster", label: "Cluster" },
            { key: "text", label: "What they said" },
            { key: "url", label: "Link" },
          ]}
          empty="No complaint language captured — widen sources or the category is genuinely quiet."
        />
      </Section>

      <Section title="Demand triggers (what makes people switch)">
        <Rows
          rows={(data.demand_triggers ?? [])}
          cols={[
            { key: "trigger", label: "Trigger" },
            { key: "source", label: "Source" },
            { key: "text", label: "Signal" },
            { key: "url", label: "Link" },
          ]}
        />
      </Section>
    </div>
  );
}

/* ------------------------------------------------------------------ tab 8 */

interface BurnInputs {
  team: number;
  engineer: number;
  founder: number;
  infra: number;
  tools: number;
  legal: number;
  runway: number;
  cash: number;
  arpa: number;
  margin: number;
}

function PatternCard({ pat }: { pat: { name: string; philosophy: string; business?: string; refine: string; worked?: string } }) {
  return (
    <Card className="p-3">
      <p className="text-sm font-medium text-zinc-200">{pat.name}</p>
      <p className="mt-1 text-xs leading-relaxed text-zinc-400">{pat.philosophy}</p>
      {pat.business && <p className="mt-1 text-xs leading-relaxed text-zinc-500">Business: {pat.business}</p>}
      <p className="mt-1 text-xs leading-relaxed text-emerald-400/80">Steal it: {pat.refine}</p>
      {pat.worked && <p className="mt-1 text-[11px] text-zinc-600">In the wild: {pat.worked}</p>}
    </Card>
  );
}

export function DnaTab({ data }: { data: DnaData }) {
  const gb = Object.entries(data.glossary_business ?? {});
  const gp = Object.entries(data.glossary_psych ?? {});
  return (
    <div className="space-y-4">
      {(data.sequencing ?? []).length > 0 && (
        <Section title="The sequencing story — what they built, in what order, and why then">
          <div className="space-y-1.5">
            {(data.sequencing ?? []).map((s, i) => (
              <div key={i} className="flex gap-3 text-xs leading-relaxed text-zinc-300">
                <span className="w-40 shrink-0 font-mono text-[10px] text-cyan-500/90">{s.when}</span>
                <span>{s.feature}</span>
              </div>
            ))}
          </div>
        </Section>
      )}

      {data.product_philosophy && (
        <Card className="p-4">
          <p className="text-sm leading-relaxed text-zinc-200">{data.product_philosophy.headline}</p>
          {(data.product_philosophy.top_patterns ?? []).map((t) => (
            <p key={t.name} className="mt-2 text-xs leading-relaxed text-zinc-500">
              <span className="text-cyan-500">{t.name}</span> ({t.mentions} evidence hits) — {t.philosophy}
            </p>
          ))}
          {(data.product_philosophy.credibility ?? []).length > 0 && (
            <div className="mt-3 rounded border border-amber-900/40 bg-amber-950/10 p-2">
              <p className="text-[11px] uppercase tracking-wider text-amber-400">credibility it earned (from live evidence)</p>
              <ul className="mt-1 space-y-1">
                {data.product_philosophy.credibility!.map((c, i) => (
                  <li key={i} className="text-xs leading-relaxed text-zinc-300">
                    {c.text}
                    {c.url && <a href={c.url} target="_blank" rel="noreferrer" className="ml-1 text-[10px] text-cyan-500/80 hover:text-cyan-400">source</a>}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </Card>
      )}

      {data.ai_insight && <LLMInsight text={data.ai_insight} />}

      {data.idea_lens && (
        <Section title={`Levers that decide winners in ${data.idea_lens.sector} — pick two`}>
          <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
            {data.idea_lens.recommended.map((pat) => <PatternCard key={pat.name} pat={pat} />)}
          </div>
          <p className="mt-2 text-xs text-zinc-500">{data.idea_lens.note}</p>
        </Section>
      )}

      {(data.features ?? []).length > 0 && (
        <Section title="Feature-by-feature: the why behind the what">
          <div className="space-y-3">
            {(data.features ?? []).map((fb) => (
              <div key={fb.feature} className="rounded-lg border border-edge p-3">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="text-sm font-medium text-zinc-200">{fb.feature}</p>
                  {fb.class && <Badge tone={fb.class === "day1" ? "green" : fb.class === "enterprise" ? "red" : "cyan"}>{fb.class}</Badge>}
                </div>
                {fb.timing && (
                  <div className="mt-2 rounded border border-cyan-900/40 bg-cyan-950/10 p-2.5">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="text-[11px] uppercase tracking-wider text-cyan-400">why then</p>
                      {fb.timing.stage && <Badge tone="zinc">{fb.timing.stage}</Badge>}
                    </div>
                    <p className="mt-1 text-xs leading-relaxed text-zinc-300">{fb.timing.major_reason}</p>
                  </div>
                )}
                <div className="mt-2 grid grid-cols-1 gap-2">
                  {fb.patterns.map((pat) => <PatternCard key={fb.feature + pat.name} pat={pat} />)}
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}

      {(gb.length > 0 || gp.length > 0) && (
        <Section title="Every term used, in plain words">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {gb.length > 0 && (
              <div>
                <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-amber-400">business terms</p>
                <ul className="space-y-1.5">
                  {gb.map(([term, def]) => (
                    <li key={term} className="text-xs leading-relaxed text-zinc-400"><span className="font-medium text-zinc-200">{term}</span> — {def}</li>
                  ))}
                </ul>
              </div>
            )}
            {gp.length > 0 && (
              <div>
                <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-cyan-400">psychology terms</p>
                <ul className="space-y-1.5">
                  {gp.map(([term, def]) => (
                    <li key={term} className="text-xs leading-relaxed text-zinc-400"><span className="font-medium text-zinc-200">{term}</span> — {def}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </Section>
      )}

      {data.note && <Warn>{data.note}</Warn>}
    </div>
  );
}
