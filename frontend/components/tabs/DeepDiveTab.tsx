"use client";

import { useState } from "react";
import type { DeepDiveData } from "@/lib/types";
import { Badge, Card, Warn } from "@/components/ui";
import { LLMInsight, Section } from "./AnalysisTabs";

function WhatTheyDo({ data }: { data: NonNullable<DeepDiveData["what_they_do"]> }) {
  const rows: { label: string; tone: string; text?: string }[] = [
    { label: "the problem, as people felt it", tone: "text-red-400", text: data.the_problem },
    { label: "what they built (the solution)", tone: "text-emerald-400", text: data.the_solution },
    { label: "what made them do it (the trigger)", tone: "text-cyan-400", text: data.the_trigger },
    { label: "the founder logic underneath", tone: "text-amber-400", text: data.founder_logic },
  ];
  const quotes = data.the_problem_in_user_words ?? [];
  return (
    <Section title="What they actually do — problem, solution, trigger">
      <Card className="space-y-3 p-4">
        {rows.map((r) =>
          r.text ? (
            <div key={r.label}>
              <p className={`text-[11px] font-semibold uppercase tracking-wider ${r.tone}`}>{r.label}</p>
              <p className="mt-0.5 text-sm leading-relaxed text-zinc-200">{r.text}</p>
            </div>
          ) : null,
        )}
        {quotes.length > 0 && (
          <div className="rounded border border-red-900/40 bg-red-950/10 p-3">
            <p className="text-[10px] uppercase tracking-wider text-red-400">in their own words (from the evidence)</p>
            <ul className="mt-1.5 space-y-2">
              {quotes.map((q, i) => (
                <li key={i} className="text-xs leading-relaxed text-zinc-300">
                  <span className="text-zinc-100">&ldquo;{q.quote}&rdquo;</span>
                  {q.source && <span className="ml-1.5 text-[10px] text-zinc-500">— {q.source}</span>}
                  {q.url && <a href={q.url} target="_blank" rel="noreferrer" className="ml-1 text-[10px] text-cyan-500/80 hover:text-cyan-400">source</a>}
                </li>
              ))}
            </ul>
          </div>
        )}
      </Card>
    </Section>
  );
}

function FeatureCard({ f }: { f: NonNullable<DeepDiveData["feature_inventory"]>[number] }) {
  const [open, setOpen] = useState(false);
  const kindTone = f.kind === "major" ? "green" : f.kind === "on-site" ? "amber" : "cyan";
  return (
    <div className="rounded-lg border border-edge p-3">
      <button onClick={() => setOpen(!open)} className="flex w-full flex-wrap items-center gap-2 text-left">
        <p className="text-sm font-medium text-zinc-200">{f.feature}</p>
        {f.kind && <Badge tone={kindTone}>{f.kind}</Badge>}
        <span className="ml-auto text-[10px] text-zinc-500">{open ? "▲ less" : "▼ the full story"}</span>
      </button>
      <p className="mt-1.5 text-xs leading-relaxed text-zinc-400">{f.what_it_does}</p>
      {open && (
        <div className="mt-2.5 space-y-2">
          <div className="rounded border border-red-900/40 bg-red-950/10 p-2.5">
            <p className="text-[10px] uppercase tracking-wider text-red-400">the issue people had before it</p>
            <p className="mt-0.5 text-xs leading-relaxed text-zinc-300">{f.the_issue_before}</p>
          </div>
          <div className="rounded border border-cyan-900/40 bg-cyan-950/10 p-2.5">
            <p className="text-[10px] uppercase tracking-wider text-cyan-400">what made them add it (the trigger)</p>
            <p className="mt-0.5 text-xs leading-relaxed text-zinc-300">{f.the_trigger}</p>
          </div>
          <div className="rounded border border-emerald-900/40 bg-emerald-950/10 p-2.5">
            <p className="text-[10px] uppercase tracking-wider text-emerald-400">the impact it made</p>
            <p className="mt-0.5 text-xs leading-relaxed text-zinc-300">{f.the_impact}</p>
          </div>
          {(f.psych_basis ?? []).length > 0 && (
            <div className="rounded border border-purple-900/40 bg-purple-950/10 p-2.5">
              <p className="text-[10px] uppercase tracking-wider text-purple-400">the psychology &amp; evolution behind it</p>
              <div className="mt-1 flex flex-wrap gap-1.5">
                {(f.psych_basis ?? []).map((p) => <Badge key={p} tone="cyan">{p}</Badge>)}
              </div>
              {f.evolution && <p className="mt-1.5 text-xs leading-relaxed text-zinc-300">{f.evolution}</p>}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Milestones({ items }: { items: NonNullable<DeepDiveData["product_milestones"]> }) {
  return (
    <Section title="Milestones that changed the product (kept out of the feature list on purpose)">
      <div className="space-y-1.5">
        {items.map((m, i) => (
          <div key={i} className="flex gap-3 text-xs leading-relaxed text-zinc-300">
            <span className="w-24 shrink-0 font-mono text-[10px] text-cyan-500/90">{m.when || "undated"}</span>
            <span>
              {m.what}
              {m.url && <a href={m.url} target="_blank" rel="noreferrer" className="ml-1 text-[10px] text-cyan-500/80 hover:text-cyan-400">source</a>}
            </span>
          </div>
        ))}
      </div>
    </Section>
  );
}

function RealityCheck({ items }: { items: NonNullable<DeepDiveData["reality_check"]>["items"] }) {
  return (
    <Section title="The reality check — what you'll actually come across (observations, not instructions)">
      <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
        {(items ?? []).map((rc) => (
          <div key={rc.area} className="rounded-lg border border-amber-900/40 bg-amber-950/10 p-3">
            <p className="text-sm font-medium text-amber-300">{rc.area}</p>
            <p className="mt-1 text-xs leading-relaxed text-zinc-300">{rc.what}</p>
          </div>
        ))}
      </div>
    </Section>
  );
}

function Marketing({ data }: { data: NonNullable<DeepDiveData["marketing"]> }) {
  const mechs = data.mechanics ?? [];
  const push = data.current_push ?? [];
  return (
    <Section title="How they actually market — the concrete mechanics detected in the evidence">
      {data.the_hook && (
        <Card className="border-cyan-900/40 bg-cyan-950/10 p-3">
          <p className="text-[11px] uppercase tracking-wider text-cyan-400">the hook — what pulls people in the door</p>
          <p className="mt-1 text-sm leading-relaxed text-zinc-200">{data.the_hook}</p>
          {push.length > 0 && (
            <p className="mt-2 text-xs text-zinc-400">
              <span className="text-cyan-500">what they&apos;re pushing right now:</span>{" "}
              {push.map((p, i) => (
                <span key={i}>{i > 0 && " · "}<span className="text-zinc-200">{p}</span></span>
              ))}
            </p>
          )}
        </Card>
      )}
      <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
        {mechs.map((m) => (
          <div key={m.mechanic} className="rounded-lg border border-edge p-3">
            <div className="flex flex-wrap items-center gap-2">
              <p className="text-sm font-medium text-zinc-200">{m.mechanic}</p>
              {m.dna_confirmed && <Badge tone="green">confirmed in dna tab</Badge>}
            </div>
            {(m.signals ?? []).length > 0 && (
              <p className="mt-1 text-[11px] text-zinc-500">evidence hits: {(m.signals ?? []).join(" · ")}</p>
            )}
            <p className="mt-1.5 text-xs leading-relaxed text-zinc-300">
              {m.how_they_used_it}
              {m.evidence_url && <a href={m.evidence_url} target="_blank" rel="noreferrer" className="ml-1 text-[10px] text-cyan-500/80 hover:text-cyan-400">source</a>}
            </p>
            <p className="mt-1.5 text-xs text-zinc-400"><span className="text-cyan-500">they promote:</span> {m.what_they_promote}</p>
            <p className="mt-1 text-xs text-zinc-500"><span className="text-purple-400">why it works:</span> {m.psych}</p>
          </div>
        ))}
        {mechs.length === 0 && (
          <p className="text-xs text-zinc-500">No marketing mechanics were visible in this run&apos;s evidence — decode with network for the full picture.</p>
        )}
      </div>
      {(data.channel_ranking ?? []).length > 0 && (
        <p className="mt-2 text-xs text-zinc-500">
          top channels for this category: <span className="text-zinc-300">{(data.channel_ranking ?? []).join(" · ")}</span>
        </p>
      )}
      {data.note && <p className="mt-1 text-xs text-zinc-600">{data.note}</p>}
    </Section>
  );
}

export function DeepDiveTab({ data }: { data: DeepDiveData }) {
  const inv = data.feature_inventory ?? [];
  const ms = data.product_milestones ?? [];
  return (
    <div className="space-y-4">
      {data.what_they_do && <WhatTheyDo data={data.what_they_do} />}

      {data.ai_insight && <LLMInsight text={data.ai_insight} />}

      {inv.length > 0 && (
        <Section title={`Every feature, major and minor (${inv.length}) — the issue before it, the trigger, the impact, the psychology`}>
          <div className="space-y-2.5">
            {inv.map((f) => <FeatureCard key={f.feature} f={f} />)}
          </div>
          <p className="mt-2 text-xs text-zinc-600">
            <span className="text-amber-400">on-site</span> = listed on the company&apos;s own pages today · each one is an option you could build differently — open a card for the full story
          </p>
        </Section>
      )}

      {ms.length > 0 && <Milestones items={ms} />}

      {data.reality_check && <RealityCheck items={data.reality_check.items} />}

      {data.marketing && <Marketing data={data.marketing} />}

      {data.note && <Warn>{data.note}</Warn>}
    </div>
  );
}
