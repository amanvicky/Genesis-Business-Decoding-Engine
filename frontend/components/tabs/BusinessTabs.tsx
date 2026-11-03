"use client";

import { useMemo, useState } from "react";
import type { DnaData, FinancialData, FrictionData, MarketSizeData, PricingData, TimelineData } from "@/lib/types";
import { Badge, Bullets, Card, Rows, Warn } from "@/components/ui";
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
  const ue = data.unit_economics;
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

      {ue && <PricingSandbox data={data} ue={ue} />}

      <Section title="Packaging psychology">
        <Rows
          rows={data.psychology ?? []}
          cols={[
            { key: "driver", label: "Driver" },
            { key: "evidence", label: "Evidence / mechanism" },
          ]}
        />
      </Section>

      <Section title="Recommended architecture (no fluff)">
        <Bullets items={data.recommendation ?? []} />
      </Section>

      {(data.history ?? []).length > 0 && (
        <Section title="Pricing archaeology (Wayback snapshots)">
          <div className="space-y-2">
            {(data.history ?? []).map((h) => (
              <Card key={h.date} className="p-3">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs text-emerald-500">{h.date}</span>
                  <a href={h.snapshot} target="_blank" rel="noreferrer" className="text-[11px] text-cyan-500/80 hover:text-cyan-400">
                    snapshot ↗
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

/* ---------------- interactive unit-economics & pricing sandbox ---------------- */

interface SandboxInputs {
  arpa: number;
  cac: number;
  churnMonthly: number; // percent
  margin: number; // 0-1
  opex: number;
}

function PricingSandbox({ data, ue }: { data: PricingData; ue: NonNullable<PricingData["unit_economics"]> }) {
  const cur = ue.currency ?? "$";
  const [inp, setInp] = useState<SandboxInputs>({
    arpa: ue.arpa ?? 29,
    cac: ue.cac_organic_proxy ?? 180,
    churnMonthly: 3,
    margin: ue.assumed_gross_margin ?? 0.82,
    opex: data.sandbox?.opex_month ?? 8000,
  });
  const [tiers, setTiers] = useState<number[]>(
    (data.tiers ?? []).map((t) => Number(String(t.price ?? "0").replace(/[^\d.]/g, "")) || 0)
  );
  const gateway = cur === "₹" ? { pct: 0.02, fixed: 0 } : { pct: 0.029, fixed: 0.3 };

  const derived = useMemo(() => {
    const m = Math.min(Math.max(inp.margin, 0), 1);
    const netMarginUnit = inp.arpa * (m - gateway.pct) - gateway.fixed;
    const ltv = inp.churnMonthly > 0 ? (netMarginUnit / inp.churnMonthly) : Infinity;
    const ltvCac = inp.cac > 0 && Number.isFinite(ltv) ? ltv / inp.cac : Infinity;
    const payback = netMarginUnit > 0 ? inp.cac / netMarginUnit : Infinity;
    const breakeven = netMarginUnit > 0 ? Math.ceil(inp.opex / netMarginUnit) : Infinity;
    const netMarginPct = inp.arpa > 0 ? ((netMarginUnit / inp.arpa) * 100) : 0;
    return { netMarginUnit, ltv, ltvCac, payback, breakeven, netMarginPct };
  }, [inp, gateway.pct, gateway.fixed]);

  const num = (v: number, digits = 0) => (Number.isFinite(v) ? v.toFixed(digits) : "—");
  const set = (k: keyof SandboxInputs) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setInp({ ...inp, [k]: Math.max(0, Number(e.target.value) || 0) });

  const field = (label: string, value: number, onChange: (e: React.ChangeEvent<HTMLInputElement>) => void, hint?: string) => (
    <label className="text-xs text-zinc-500">
      {label}
      <input
        type="number"
        min={0}
        step="any"
        value={value}
        onChange={onChange}
        className="mt-1 w-full rounded border border-edge bg-base px-2 py-1 font-mono text-sm text-zinc-200 outline-none focus:border-emerald-800/70"
      />
      {hint && <span className="mt-0.5 block text-[10px] text-zinc-700">{hint}</span>}
    </label>
  );

  return (
    <Section title="Unit-economics & pricing sandbox (edit any cell — margins shift live)">
      <div className="grid grid-cols-2 gap-3 rounded-lg border border-edge bg-panel/40 p-3 sm:grid-cols-5">
        {field(`ARPA (${cur})`, inp.arpa, set("arpa"), "avg revenue per account / mo")}
        {field("CAC", inp.cac, set("cac"), "acquisition cost per customer")}
        {field("Churn % /mo", inp.churnMonthly, set("churnMonthly"), "logo churn per month")}
        {field("Gross margin 0-1", inp.margin, set("margin"), "before gateway drag")}
        {field(`Opex /mo (${cur})`, inp.opex, set("opex"), "from burn calculator")}
      </div>

      <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
        {[
          [`LTV (${cur})`, num(derived.ltv), derived.ltvCac >= 3 ? "green" : "red"],
          ["LTV : CAC", `${num(derived.ltvCac, 2)}×`, derived.ltvCac >= 3 ? "green" : "red"],
          ["CAC payback", `${num(derived.payback, 1)} mo`, derived.payback <= 12 ? "green" : "amber"],
          ["Breakeven customers", num(derived.breakeven), "cyan"],
        ].map(([k, v, tone]) => (
          <div key={k} className="rounded border border-edge bg-zinc-900/40 p-2">
            <p className="text-[10px] uppercase tracking-wider text-zinc-600">{k}</p>
            <p className={`font-mono text-base ${tone === "green" ? "text-emerald-400" : tone === "red" ? "text-red-400" : tone === "amber" ? "text-amber-400" : "text-cyan-400"}`}>
              {v}
            </p>
          </div>
        ))}
      </div>

      {tiers.length > 0 && (
        <div className="mt-3 rounded-lg border border-edge bg-panel/40 p-3">
          <p className="text-xs text-zinc-500">
            Per-tier price stress test — net margin after gateway drag ({(gateway.pct * 100).toFixed(1)}%
            {gateway.fixed ? ` + ${cur}${gateway.fixed}` : ""}):
          </p>
          <div className="mt-2 space-y-2">
            {(data.tiers ?? []).map((t, i) => {
              const price = tiers[i] ?? 0;
              const net = price * (1 - gateway.pct) - gateway.fixed;
              const netPct = price > 0 ? (net / price) * 100 : 0;
              return (
                <div key={i} className="flex items-center gap-3">
                  <span className="w-24 shrink-0 truncate text-xs text-zinc-400">{t.name}</span>
                  <input
                    type="number"
                    min={0}
                    value={price}
                    onChange={(e) => setTiers(tiers.map((v, j) => (j === i ? Math.max(0, Number(e.target.value) || 0) : v)))}
                    className="w-24 rounded border border-edge bg-base px-2 py-1 font-mono text-xs text-zinc-200 outline-none focus:border-emerald-800/70"
                  />
                  <div className="h-2.5 flex-1 overflow-hidden rounded bg-zinc-900">
                    <div
                      className={`h-full rounded transition-all duration-300 ${netPct > 70 ? "bg-emerald-500/70" : netPct > 40 ? "bg-amber-500/70" : "bg-red-500/70"}`}
                      style={{ width: `${Math.max(0, Math.min(100, netPct))}%` }}
                    />
                  </div>
                  <span className="w-16 shrink-0 text-right font-mono text-xs text-zinc-400">{netPct.toFixed(0)}%</span>
                </div>
              );
            })}
          </div>
          <p className="mt-2 text-[11px] text-zinc-600">
            Structural margin shift: raising a low-tier price moves net margin most (fixed gateway fee is proportionally
            larger there); cutting enterprise-tier price changes almost nothing unless seat volume follows.
          </p>
        </div>
      )}
    </Section>
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

export function FinancialTab({ data }: { data: FinancialData }) {
  const cur = data.currency ?? "$";
  const c = data.computed ?? {};
  const [inp, setInp] = useState<BurnInputs>({
    team: data.team_size ?? 3,
    engineer: Math.round((data.salary_engineer_loaded ?? 155000) / 12),
    founder: Math.round((data.salary_founder_draw ?? 90000) / 12),
    infra: data.infra_month ?? 250,
    tools: Math.round(data.tools_month ?? 120),
    legal: Math.round((data.legal_year ?? 4000) / 12),
    runway: data.runway_target_months ?? 12,
    cash: 0,
    arpa: c.arpa_assumption ?? 29,
    margin: c.gross_margin_assumption ?? 0.82,
  });

  const derived = useMemo(() => {
    const payroll = inp.founder + inp.team * inp.engineer;
    const burn = payroll + inp.infra + inp.tools + inp.legal;
    const capital = burn * inp.runway;
    const marginRevenue = inp.arpa * inp.margin;
    const breakeven = marginRevenue > 0 ? Math.ceil(burn / marginRevenue) : Infinity;
    const runwayMonths = burn > 0 ? inp.cash / burn : Infinity;
    return { payroll, burn, capital, breakeven, runwayMonths };
  }, [inp]);

  const count = (n: number) => (Number.isFinite(n) ? String(n) : "—");

  const field = (key: keyof BurnInputs, label: string) => (
    <label className="text-xs text-zinc-500">
      {label}
      <input
        type="number"
        min={0}
        value={inp[key]}
        onChange={(e) => setInp({ ...inp, [key]: Math.max(0, Number(e.target.value) || 0) })}
        className="mt-1 w-full rounded border border-edge bg-base px-2 py-1 font-mono text-sm text-zinc-200 outline-none focus:border-emerald-800/70"
      />
    </label>
  );

  const money = (n: number) => `${cur}${Math.round(n).toLocaleString()}`;

  return (
    <div className="space-y-4">
      {data.ai_insight && <LLMInsight text={data.ai_insight} />}

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        {[
          ["Monthly burn", money(derived.burn), "red"],
          ["Capital for target", money(derived.capital), "amber"],
          ["Breakeven customers", count(derived.breakeven), "cyan"],
          ["Cash runway", inp.cash > 0 && Number.isFinite(derived.runwayMonths) ? `${Math.floor(derived.runwayMonths)} mo` : "set cash →", "green"],
        ].map(([k, v, tone]) => (
          <Card key={k} className="p-3">
            <p className="text-[10px] uppercase tracking-wider text-zinc-600">{k}</p>
            <p className={`font-mono text-base ${tone === "red" ? "text-red-400" : tone === "amber" ? "text-amber-400" : tone === "cyan" ? "text-cyan-400" : "text-emerald-400"}`}>{v}</p>
          </Card>
        ))}
      </div>

      <Section title="Calculator (edit any cell — recomputes live)">
        <div className="grid grid-cols-2 gap-3 rounded-lg border border-edge bg-panel/40 p-3 sm:grid-cols-5">
          {field("team", "Team size")}
          {field("engineer", `Eng. salary /mo (loaded)`)}
          {field("founder", "Founder draw /mo")}
          {field("infra", "Infra /mo")}
          {field("tools", "Tools /mo")}
          {field("legal", "Legal+compliance /mo")}
          {field("runway", "Runway target (mo)")}
          {field("cash", `Cash on hand (${cur})`)}
          {field("arpa", `ARPA assumption (${cur})`)}
          {field("margin", "Gross margin (0-1)")}
        </div>
        <p className="mt-2 text-xs text-zinc-600">
          burn = founder draw + team×engineer + infra + tools + legal/12 · breakeven = burn / (ARPA × margin)
        </p>
      </Section>

      {(data.sensitivity ?? []).length > 0 && (
        <Section title="Sensitivity (what actually moves the number)">
          <Rows
            rows={(data.sensitivity ?? [])}
            cols={[
              { key: "scenario", label: "Scenario" },
              { key: "burn_delta", label: "Burn delta" },
            ]}
          />
        </Section>
      )}

      {(data.warnings ?? []).length > 0 && (
        <Section title="Zero-sugarcoating warnings">
          <div className="space-y-2">
            {(data.warnings ?? []).map((w, i) => (
              <Warn key={i}>{w}</Warn>
            ))}
          </div>
        </Section>
      )}
    </div>
  );
}

export function MarketSizeTab({ data }: { data: MarketSizeData }) {
  const tone = data.verdict_tone === "green" ? "green" : data.verdict_tone === "red" ? "red" : "amber";
  const cap = data.capital_strategy;
  return (
    <div className="space-y-4">
      <Card className="p-4">
        <div className="flex items-start justify-between gap-4">
          <p className="text-sm text-zinc-300">{data.verdict ?? "—"}</p>
          <Badge tone={tone}>market math</Badge>
        </div>
        {data.market_base && (
          <p className="mt-2 text-xs text-zinc-600">
            base: {data.market_base.buying_units?.toLocaleString()} {data.market_base.unit} ({data.market_base.sector}/
            {data.market_base.geography}) · ARPA {data.assumptions?.arpa} ({data.assumptions?.arpa_source})
          </p>
        )}
      </Card>

      {data.ai_insight && <LLMInsight text={data.ai_insight} />}

      <Section title="TAM / SAM / SOM — bottom-up, formulas shown">
        <div className="grid grid-cols-1 gap-3 lg:grid-cols-3">
          {[["TAM", data.tam], ["SAM (wedge)", data.sam]].map(([label, tier]) => (
            <div key={label as string} className="rounded-lg border border-cyan-900/50 bg-cyan-950/10 p-3">
              <p className="text-xs font-semibold uppercase tracking-wider text-cyan-400">{label as string}</p>
              <p className="mt-1 text-2xl font-semibold text-zinc-100">{(tier as NonNullable<typeof data.tam>)?.display ?? "—"}</p>
              <p className="mt-1 text-[11px] leading-relaxed text-zinc-600">{(tier as NonNullable<typeof data.tam>)?.basis}</p>
            </div>
          ))}
          <div className="rounded-lg border border-emerald-900/50 bg-emerald-950/10 p-3">
            <p className="text-xs font-semibold uppercase tracking-wider text-emerald-400">SOM (3-year, earned)</p>
            <p className="mt-1 text-2xl font-semibold text-zinc-100">{data.som_by_year?.[data.som_by_year.length - 1]?.display ?? "—"}</p>
            <ul className="mt-1 space-y-0.5">
              {(data.som_by_year ?? []).map((y) => (
                <li key={y.year} className="text-[11px] text-zinc-500">
                  {y.year}: {y.display} · {y.customers.toLocaleString()} customers @ {y.adoption} adoption
                </li>
              ))}
            </ul>
          </div>
        </div>
        <Bullets items={data.formulas ?? []} />
      </Section>

      {cap && (
        <Section title="Capital strategy — raise vs bootstrap">
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <Card className="p-4">
              <p className="text-xs uppercase tracking-wider text-zinc-500">recommended raise (18 months)</p>
              <p className="mt-1 text-2xl font-semibold text-zinc-100">
                {cap.recommended_raise
                  ? `${data.assumptions?.currency === "₹" ? "₹" : "$"}${cap.recommended_raise.toLocaleString()}`
                  : "—"}
              </p>
              <p className="mt-1 text-[11px] text-zinc-600">{cap.raise_formula}</p>
              {cap.dilution_at_geo_cap_pct != null && (
                <p className="mt-2 text-xs text-zinc-400">
                  ≈ <span className="text-amber-400">{cap.dilution_at_geo_cap_pct}% dilution</span> at the geo-typical
                  pre-seed cap <span className="text-zinc-600">({cap.dilution_formula})</span>
                </p>
              )}
              <p className="mt-2 text-xs leading-relaxed text-emerald-400/80">{cap.raise_when}</p>
            </Card>
            <Card className="p-4">
              <p className="text-xs uppercase tracking-wider text-zinc-500">bootstrap benchmark</p>
              <p className="mt-2 text-xs leading-relaxed text-zinc-300">{cap.bootstrap_note}</p>
              {cap.geo_norms?.note && <p className="mt-2 text-[11px] text-zinc-600">{cap.geo_norms.note}</p>}
            </Card>
          </div>
        </Section>
      )}

      {data.founder_market_fit && (
        <Section title="Founder-market fit — score honestly">
          <p className="mb-2 text-xs text-zinc-500">{data.founder_market_fit.instruction}</p>
          <ul className="space-y-1.5">
            {(data.founder_market_fit.questions ?? []).map((q, i) => (
              <li key={i} className="flex gap-3 text-sm text-zinc-300">
                <span className="w-16 shrink-0 text-right font-mono text-[10px] uppercase text-zinc-600">{q.weight}</span>
                <span>{q.q}</span>
              </li>
            ))}
          </ul>
        </Section>
      )}

      {data.investor_question_map && (
        <Section title="Every investor question — answered by a tab in this dossier">
          <Rows
            rows={(data.investor_question_map ?? []).map((r) => ({ question: r.question, answered_by: r.answered_by }))}
            cols={[
              { key: "question", label: "The question" },
              { key: "answered_by", label: "Answered by" },
            ]}
            empty=""
          />
        </Section>
      )}

      {(data.evidence_money_signals ?? []).length > 0 && (
        <Section title="Market numbers seen in live evidence">
          <ul className="space-y-1.5">
            {(data.evidence_money_signals ?? []).map((m, i) => (
              <li key={i} className="text-xs text-zinc-400">
                <span className="font-mono text-emerald-500">{m.raw}</span> — {m.context}
              </li>
            ))}
          </ul>
        </Section>
      )}

      {data.note && <Warn>{data.note}</Warn>}
    </div>
  );
}


function PatternCard({ pat }: { pat: NonNullable<DnaData["features"]>[number]["patterns"][number] }) {
  return (
    <div className="rounded-lg border border-edge bg-panel/60 p-3">
      <p className="text-xs font-semibold uppercase tracking-wider text-cyan-400">{pat.name}</p>
      <p className="mt-2 text-xs leading-relaxed text-zinc-300"><span className="text-emerald-500">philosophy:</span> {pat.philosophy}</p>
      <div className="mt-2">
        <p className="text-[11px] uppercase tracking-wider text-zinc-500">psychology at work</p>
        <ul className="mt-1 space-y-1">
          {pat.psychology.map((ps) => (
            <li key={ps.principle} className="text-xs leading-relaxed text-zinc-400">
              <span className="font-medium text-zinc-200">{ps.principle}</span> — {ps.explained}
            </li>
          ))}
        </ul>
      </div>
      <p className="mt-2 text-xs leading-relaxed text-zinc-300"><span className="text-amber-500">business:</span> {pat.business}</p>
      <p className="mt-2 text-xs leading-relaxed text-emerald-400/90"><span className="text-emerald-600">steal it:</span> {pat.refine}</p>
    </div>
  );
}

export function DnaTab({ data }: { data: DnaData }) {
  const gb = Object.entries(data.glossary_business ?? {});
  const gp = Object.entries(data.glossary_psych ?? {});
  return (
    <div className="space-y-4">
      {data.product_philosophy && (
        <Card className="p-4">
          <p className="text-sm leading-relaxed text-zinc-200">{data.product_philosophy.headline}</p>
          {(data.product_philosophy.top_patterns ?? []).map((t) => (
            <p key={t.name} className="mt-2 text-xs leading-relaxed text-zinc-500">
              <span className="text-cyan-500">{t.name}</span> ({t.mentions} evidence hits) — {t.philosophy}
            </p>
          ))}
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
