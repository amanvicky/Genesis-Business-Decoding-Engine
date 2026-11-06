"use client";

import type { ComplianceData, FeaturesData, PremortemData, StructuralData } from "@/lib/types";
import { Badge, Bullets, Card, Rows, Sev, Warn } from "@/components/ui";

export function StructuralTab({ data }: { data: StructuralData }) {
  const score = data.verdict_score ?? 0;
  const tone = score >= 55 ? "green" : score >= 30 ? "amber" : "red";
  return (
    <div className="space-y-4">
      <Card className="p-4">
        <div className="flex items-start justify-between gap-4">
          <p className="text-sm text-zinc-300">{data.verdict ?? "—"}</p>
          <Badge tone={tone}>signal {score}/100</Badge>
        </div>
        {data.evidence_volume && (
          <p className="mt-2 text-xs text-zinc-600">
            evidence: {data.evidence_volume.search_results ?? 0} web · {data.evidence_volume.hn_stories ?? 0} HN · {data.evidence_volume.reddit_posts ?? 0} Reddit · {data.evidence_volume.review_snippets ?? 0} review snippets
          </p>
        )}
      </Card>

      {data.ai_insight && <LLMInsight text={data.ai_insight} />}

      <Section title="Pain points (as voiced publicly)">
        <Rows
          rows={data.pain_points ?? []}
          cols={[
            { key: "source", label: "Source" },
            { key: "text", label: "Voice" },
            { key: "url", label: "Link" },
          ]}
          empty="No pain-language surfaced — either too early/niche, or the pain lives offline. Interview before building."
        />
      </Section>

      <Section title="Demand triggers">
        <Rows
          rows={data.demand_triggers ?? []}
          cols={[
            { key: "source", label: "Source" },
            { key: "text", label: "Signal" },
            { key: "url", label: "Link" },
          ]}
        />
      </Section>

      {data.core_mechanics && data.core_mechanics.length > 0 && (
        <Section title="Core mechanics (how money moves)">
          <Bullets items={data.core_mechanics} />
        </Section>
      )}

      <Section title="Systemic moats with evidence">
        <Rows
          rows={(data.moats ?? [])}
          cols={[
            { key: "type", label: "Moat type" },
            { key: "evidence", label: "Evidence" },
          ]}
          empty="No moat-type evidence found in public corpus — assume none exists yet."
        />
      </Section>

      <Section title="Market timing shifts">
        <Rows
          rows={(data.timing_shifts ?? [])}
          cols={[
            { key: "shift", label: "Shift" },
            { key: "implication", label: "Implication" },
          ]}
          empty="No inflection signals detected."
        />
      </Section>
    </div>
  );
}

export function FeaturesTab({ data }: { data: FeaturesData }) {
  const cc = data.class_counts ?? {};
  return (
    <div className="space-y-4">
      <Card className="p-4">
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <Badge tone="green">{cc["day1"] ?? 0} Day-1 class</Badge>
          <Badge tone="cyan">{cc["growth"] ?? 0} growth-era</Badge>
          <Badge tone="amber">{cc["enterprise"] ?? 0} enterprise-tier</Badge>
          {data.founded_year && <Badge>founded {data.founded_year}</Badge>}
        </div>
        <p className="mt-3 text-sm text-zinc-300">
          <span className="text-zinc-500">True USP candidate:</span> {data.true_usp ?? "—"}
        </p>
      </Card>

      {data.alternatives && ((data.alternatives.candidates?.length ?? 0) > 0 || (data.alternatives.chatter?.length ?? 0) > 0) && (
        <Section title="Who already does this — candidate alternatives (mined from live evidence, verify each)">
          {(data.alternatives.candidates?.length ?? 0) > 0 && (
            <div className="mb-3 flex flex-wrap gap-2">
              {data.alternatives.candidates!.map((n) => (
                <Badge key={n} tone="cyan">{n}</Badge>
              ))}
            </div>
          )}
          <ul className="space-y-2">
            {(data.alternatives.chatter ?? []).map((c, i) => (
              <li key={i} className="text-xs leading-relaxed text-zinc-300">
                {c.text}{" "}
                {c.url && (
                  <a href={c.url} target="_blank" rel="noreferrer" className="text-[11px] text-cyan-500/80 hover:text-cyan-400">
                    source
                  </a>
                )}
              </li>
            ))}
          </ul>
        </Section>
      )}

      {data.ai_insight && <LLMInsight text={data.ai_insight} />}

      {data.binary_roadmap && (
        <Section title="Binary roadmap (v2 decompiler): build / later / do-not-build">
          <div className="grid grid-cols-1 gap-3 lg:grid-cols-3">
            <div className="rounded-lg border border-emerald-900/50 bg-emerald-950/10 p-3">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-emerald-400">▶ build now</p>
              <ul className="space-y-2">
                {(data.binary_roadmap.build_now ?? []).map((r, i) => (
                  <li key={i} className="text-xs leading-relaxed text-zinc-300">
                    <span className="text-emerald-500">•</span> {r.feature}
                    <span className="block text-[11px] text-zinc-600">{r.why}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-lg border border-amber-900/50 bg-amber-950/10 p-3">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-amber-400">◷ later (post-PMF)</p>
              <ul className="space-y-2">
                {(data.binary_roadmap.build_later ?? []).map((r, i) => (
                  <li key={i} className="text-xs leading-relaxed text-zinc-400">
                    <span className="text-amber-500">•</span> {r.feature}
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-lg border border-red-900/50 bg-red-950/10 p-3">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-red-400">✗ do NOT build (bloat)</p>
              <ul className="space-y-2">
                {(data.binary_roadmap.never_for_mvp ?? []).map((r, i) => (
                  <li key={i} className="text-xs leading-relaxed text-zinc-400">
                    <span className="text-red-500">•</span> {r.feature}
                    <span className="block text-[11px] text-zinc-600">gate: {r.gate}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </Section>
      )}

      <Section title="MVP build sequence">
        <ol className="space-y-1.5">
          {(data.mvp_sequence ?? []).map((s) => (
            <li key={s.order} className="flex gap-3 text-sm text-zinc-300">
              <span className="w-5 shrink-0 text-right font-mono text-xs text-emerald-500">{s.order}</span>
              <span>{s.build}</span>
            </li>
          ))}
        </ol>
      </Section>

      <Section title="Decompiled feature history (chronological)">
        <Rows
          rows={(data.features ?? [])}
          cols={[
            { key: "date", label: "Date" },
            { key: "feature", label: "Feature" },
            { key: "class", label: "Class" },
            { key: "source", label: "Source" },
          ]}
          empty="No changelog/releases found — for private companies this data lives in blogs and funding announcements."
        />
      </Section>

      <Section title="Distinctive language (USP mining)">
        <div className="flex flex-wrap gap-2">
          {(data.usp_candidates ?? []).map((u) => (
            <span key={u.phrase} className="rounded border border-edge bg-zinc-900/50 px-2 py-1 text-xs text-zinc-400">
              {u.phrase} <span className="text-zinc-600">×{u.mentions}</span>
            </span>
          ))}
        </div>
      </Section>
    </div>
  );
}

export function ComplianceTab({ data }: { data: ComplianceData }) {
  return (
    <div className="space-y-4">
      <Card className="p-4">
        <div className="flex items-center justify-between">
          <p className="text-sm text-zinc-300">
            {data.sector_detected} ·{" "}
            {data.jurisdictions?.us && data.jurisdictions?.india ? "US + India (global)" : data.jurisdictions?.us ? "United States" : "India"}
          </p>
          <Badge tone="red">{data.critical_count ?? 0} launch-blocking</Badge>
        </div>
        {data.disclaimer && <p className="mt-2 text-xs text-zinc-600">{data.disclaimer}</p>}
      </Card>

      {data.ai_insight && <LLMInsight text={data.ai_insight} />}

      <Section title="Do-now checklist (severity-ordered)">
        <Rows
          rows={(data.checklist ?? [])}
          cols={[
            { key: "order", label: "#" },
            { key: "item", label: "Obligation" },
            { key: "cost", label: "Cost" },
            { key: "time", label: "Window" },
          ]}
        />
      </Section>

      <Section title="Landmine register">
        <div className="space-y-2">
          {(data.landmines ?? []).map((l, i) => (
            <Card key={i} className="p-3">
              <div className="flex items-start justify-between gap-3">
                <p className="text-sm font-medium text-zinc-300">{l.item}</p>
                <Sev severity={l.severity} />
              </div>
              <p className="mt-1 text-xs leading-relaxed text-zinc-500">{l.why}</p>
              <p className="mt-1 text-xs text-zinc-600">
                <span className="text-zinc-500">cost:</span> {l.cost} · <span className="text-zinc-500">window:</span> {l.time}
              </p>
            </Card>
          ))}
        </div>
      </Section>

      {data.us_payroll_matrix && (
        <Section title="US payroll-engine matrix (state × obligation)">
          <Rows
            rows={data.us_payroll_matrix}
            cols={[
              { key: "state", label: "State" },
              { key: "income_tax", label: "Income tax" },
              { key: "sui_new", label: "SUI (new)" },
              { key: "sdi", label: "SDI/FLI" },
              { key: "paid_leave", label: "Paid leave" },
              { key: "final_pay", label: "Final pay" },
              { key: "gotcha", label: "Gotcha" },
            ]}
          />
        </Section>
      )}

      {data.us_state_matrix && (
        <Section title="US state burden matrix">
          <Rows
            rows={data.us_state_matrix}
            cols={[
              { key: "state", label: "State" },
              { key: "burden", label: "Burden" },
              { key: "notes", label: "Notes" },
            ]}
          />
          {data.us_expansion_order && (
            <p className="mt-2 text-xs text-zinc-600">
              Expansion order: {(data.us_expansion_order ?? []).map((e) => e.state).join(" → ")}
            </p>
          )}
        </Section>
      )}

      {data.india_state_notes && (
        <Section title="India state notes">
          <Rows
            rows={data.india_state_notes}
            cols={[
              { key: "state", label: "State" },
              { key: "note", label: "Statutory notes" },
            ]}
          />
        </Section>
      )}
    </div>
  );
}

export function PremortemTab({ data }: { data: PremortemData }) {
  return (
    <div className="space-y-4">
      {data.ai_insight && <LLMInsight text={data.ai_insight} />}

      <Section title="Dominant death patterns in this domain">
        <div className="space-y-2">
          {(data.common_failure_modes ?? []).map((m, i) => (
            <Card key={i} className="p-3">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-red-400/90">{m.mode}</p>
                <Badge tone="red">{m.analogs_affected} analogs</Badge>
              </div>
              <p className="mt-1 text-xs leading-relaxed text-zinc-400">{m.counter}</p>
            </Card>
          ))}
        </div>
      </Section>

      <Section title="Failure post-mortems (operational, not press-release)">
        <div className="space-y-3">
          {(data.analogs ?? []).map((a, i) => (
            <Card key={i} className="p-4">
              <div className="flex items-baseline justify-between gap-3">
                <p className="text-sm font-semibold text-zinc-200">{a.name}</p>
                <span className="text-xs text-zinc-600">
                  {a.domain} · {a.years}
                </span>
              </div>
              <p className="mt-2 text-xs leading-relaxed text-zinc-400">{a.what_happened}</p>
              <dl className="mt-2 space-y-1 text-xs">
                <div>
                  <dt className="inline text-red-400/80">Root cause: </dt>
                  <dd className="inline text-zinc-400">{a.root_cause}</dd>
                </div>
                <div>
                  <dt className="inline text-amber-400/80">Operational flaw: </dt>
                  <dd className="inline text-zinc-400">{a.operational_flaw}</dd>
                </div>
                <div>
                  <dt className="inline text-emerald-400/80">Lesson: </dt>
                  <dd className="inline text-zinc-400">{a.lesson}</dd>
                </div>
              </dl>
            </Card>
          ))}
        </div>
      </Section>

      {data.field_reports && data.field_reports.length > 0 && (
        <Section title="Field reports (searched live)">
          <Rows
            rows={data.field_reports}
            cols={[
              { key: "title", label: "Report" },
              { key: "snippet", label: "Excerpt" },
              { key: "url", label: "Link" },
            ]}
          />
        </Section>
      )}

      <Section title="Pre-mortem questions (answer in writing)">
        <Bullets items={data.premortem_questions ?? []} />
      </Section>
    </div>
  );
}

export function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h4 className="mb-2 text-xs uppercase tracking-wider text-zinc-500">{title}</h4>
      {children}
    </div>
  );
}

export function LLMInsight({ text }: { text: string }) {
  return (
    <div className="rounded-lg border border-cyan-900/50 bg-cyan-950/15 p-3">
      <p className="mb-1 text-[10px] uppercase tracking-wider text-cyan-600">local-LLM sharpening (Ollama)</p>
      <p className="whitespace-pre-wrap text-sm leading-relaxed text-cyan-100/80">{text}</p>
    </div>
  );
}

export { Warn };
