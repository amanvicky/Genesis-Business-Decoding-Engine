"use client";

import type { DarkWebData, DistributionData, PlaybookData, TechArchData } from "@/lib/types";
import { Badge, Bullets, Card, CodeBlock, Rows, Warn } from "@/components/ui";
import { LLMInsight, Section } from "./AnalysisTabs";

export function DistributionTab({ data }: { data: DistributionData }) {
  return (
    <div className="space-y-4">
      {data.ai_insight && <LLMInsight text={data.ai_insight} />}
      <div className="space-y-3">
        {(data.channels ?? []).map((ch, i) => (
          <Card key={i} className="p-4">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <p className="text-sm font-medium text-zinc-200">{ch.name}</p>
              <div className="flex gap-2">
                <Badge tone="cyan">{ch.effort}</Badge>
                <Badge>first signal: {ch.time_to_first_signal}</Badge>
                {(ch.corpus_signal ?? 0) > 0 && <Badge tone="green">corpus signal ×{ch.corpus_signal}</Badge>}
              </div>
            </div>
            <p className="mt-2 text-xs leading-relaxed text-zinc-400">
              <span className="text-emerald-500/80">loop:</span> {ch.loop}
            </p>
            <Bullets className="mt-2" items={ch.actions ?? []} />
          </Card>
        ))}
      </div>
      <Section title="Operating rules">
        <Bullets items={data.strategy ?? []} />
      </Section>
    </div>
  );
}

export function TechArchTab({ data }: { data: TechArchData }) {
  return (
    <div className="space-y-4">
      {data.ai_insight && <LLMInsight text={data.ai_insight} />}

      <Section title="System architecture">
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          {Object.entries(data.architecture ?? {}).map(([k, v]) => (
            <div key={k} className="rounded-lg border border-edge bg-zinc-900/40 p-3 transition-colors duration-200 hover:border-zinc-700">
              <p className="text-[10px] uppercase tracking-wider text-emerald-600">{k}</p>
              <p className="mt-1 text-xs text-zinc-300">{v}</p>
            </div>
          ))}
        </div>
      </Section>

      <Section title="Stack layers">
        <Bullets items={data.stack ?? []} />
      </Section>

      <Section title="Load-bearing decisions">
        <Rows
          rows={(data.decisions ?? [])}
          cols={[
            { key: "decision", label: "Decision" },
            { key: "why", label: "Why" },
          ]}
        />
      </Section>

      <Section title="Starter scaffolding (copied into the ZIP export)">
        <div className="space-y-3">
          {(data.files ?? []).map((f, i) => (
            <CodeBlock key={i} path={f.path ?? "file"} language={f.language} content={f.content ?? ""} />
          ))}
        </div>
      </Section>
    </div>
  );
}

export function DarkWebTab({ data }: { data: DarkWebData }) {
  if (data.skipped) {
    return <Warn>{data.reason ?? "Module skipped."}</Warn>;
  }
  const tor = data.tor ?? {};
  return (
    <div className="space-y-4">
      <Card className="p-4">
        <div className="flex items-center justify-between">
          <p className="text-sm text-zinc-300">
            Tor circuit:{" "}
            {tor.available ? (
              <span className="text-emerald-400">
                live{tor.exit_ip ? ` (exit ${tor.exit_ip})` : ""} · {tor.proxy}
              </span>
            ) : (
              <span className="text-amber-400">offline — degraded to clearnet OSINT</span>
            )}
          </p>
          {tor.available ? <Badge tone="green">socks5 routing</Badge> : <Badge tone="amber">clearnet fallback</Badge>}
        </div>
        {!tor.available && tor.reason && <p className="mt-1 text-xs text-zinc-600">{tor.reason}</p>}
      </Card>

      <Warn>{data.ethics_notice}</Warn>

      {(data.breaches ?? []).length > 0 && (
        <Section title="Breach-corpus matches (HIBP free corpus)">
          <Rows
            rows={(data.breaches ?? [])}
            cols={[
              { key: "name", label: "Breach" },
              { key: "date", label: "Date" },
              { key: "accounts", label: "Accounts" },
              { key: "data_classes", label: "Data" },
            ]}
          />
        </Section>
      )}

      <Section title="Raw findings (passive reads)">
        <Rows
          rows={(data.findings ?? [])}
          cols={[
            { key: "risk", label: "Risk" },
            { key: "source", label: "Source" },
            { key: "title", label: "Title" },
            { key: "url", label: "Link" },
          ]}
          empty="No indexed dark-web/paste chatter matched this subject."
        />
      </Section>

      <Section title="Defensive guidance">
        <Bullets items={data.guidance ?? []} />
      </Section>
    </div>
  );
}

export function PlaybookTab({ data }: { data: PlaybookData }) {
  return (
    <div className="space-y-4">
      {data.ai_insight && <LLMInsight text={data.ai_insight} />}

      {(data.phases ?? []).map((p, i) => (
        <Card key={i} className="p-4">
          <p className="text-sm font-medium text-emerald-400/90">{p.phase}</p>
          <ol className="mt-2 space-y-2">
            {p.steps.map((s, j) => {
              if (typeof s === "string") {
                return (
                  <li key={j} className="flex gap-2 text-sm text-zinc-400">
                    <span className="shrink-0 font-mono text-xs text-zinc-600">{j + 1}.</span>
                    <span>{s}</span>
                  </li>
                );
              }
              const label = s.action ?? s.step ?? s.hurdle ?? s.strategy ?? "";
              const meta = [s.cost, s.window, s.fix, s.time].filter(Boolean).join(" · ");
              return (
                <li key={j} className="flex gap-2 text-sm text-zinc-400">
                  <span className="shrink-0 font-mono text-xs text-zinc-600">{j + 1}.</span>
                  <span>
                    {label}
                    {meta && <span className="block text-xs text-zinc-600">{meta}</span>}
                  </span>
                </li>
              );
            })}
          </ol>
          {p.hurdle && (
            <p className="mt-2 border-t border-edge pt-2 text-xs text-amber-400/80">
              <span className="uppercase tracking-wider text-zinc-600">hurdle: </span>
              {p.hurdle}
            </p>
          )}
        </Card>
      ))}

      <Section title="KYC document pack (prepare before gateway application)">
        <div className="flex flex-wrap gap-2">
          {(data.kyc_docs ?? []).map((d) => (
            <span key={d} className="rounded border border-edge bg-zinc-900/50 px-2 py-1 text-xs text-zinc-400">
              {d}
            </span>
          ))}
        </div>
      </Section>

      <Section title="Kill criteria (when to stop)">
        <Bullets items={data.kill_criteria ?? []} />
      </Section>

      {data.note && <p className="text-xs italic text-zinc-600">{data.note}</p>}
    </div>
  );
}
