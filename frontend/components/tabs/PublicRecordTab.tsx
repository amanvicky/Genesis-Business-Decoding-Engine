"use client";

import type { PublicRecordData, RegistryRow } from "@/lib/types";
import { Badge, Card, Rows, Warn } from "@/components/ui";
import { LLMInsight, Section } from "./AnalysisTabs";

function Fact({ label, value, source }: { label: string; value?: string | null; source?: string | null }) {
  if (!value) return null;
  return (
    <div className="flex flex-wrap items-baseline gap-x-3 gap-y-0.5 py-1">
      <span className="w-44 shrink-0 text-xs uppercase tracking-wider text-zinc-500">{label}</span>
      <span className="min-w-0 flex-1 break-words font-mono text-sm text-zinc-200">{value}</span>
      {source && (
        <a href={source} target="_blank" rel="noreferrer" className="text-[11px] text-cyan-500/80 hover:text-cyan-400">
          source
        </a>
      )}
    </div>
  );
}

export function PublicRecordTab({ data }: { data: PublicRecordData }) {
  const li = data.legal_identity ?? {};
  const dr = data.domain_record ?? null;
  const edgar = data.edgar ?? null;
  const wd = data.wikidata ?? null;
  const regs: readonly RegistryRow[] = data.registrations ?? [];
  const site = data.site ?? null;
  const edgarLink = edgar?.cik
    ? `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=${edgar.cik}&type=10-K`
    : null;
  const hasLegal =
    !!(li.legal_name || li.registration_no || li.registered_office || li.incorporation || li.tax_id || li.address_jsonld);

  return (
    <div className="space-y-4">
      <Card className="p-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="text-sm text-zinc-300">
            {data.domain ? (
              <>
                everything publicly on file for <span className="font-mono text-amber-400">{data.domain}</span>
              </>
            ) : (
              "the public registry layer"
            )}
          </p>
          <div className="flex flex-wrap gap-2">
            {li.registration_no && <Badge tone="green">{li.registration_kind ?? "registered"}</Badge>}
            {li.tax_id && <Badge tone="cyan">{li.tax_id_kind ?? "tax id"}</Badge>}
            {edgar?.ticker && <Badge tone="cyan">EDGAR {edgar.ticker}</Badge>}
          </div>
        </div>
        {site && (
          <p className="mt-2 text-xs text-zinc-600">
            primary source read directly: {site.title || data.domain}
            {(site.tech ?? []).length > 0 && <> · stack: {(site.tech ?? []).slice(0, 6).join(", ")}</>}
          </p>
        )}
        {data.note && <p className="mt-2 text-xs text-zinc-600">{data.note}</p>}
      </Card>

      {data.ai_insight && <LLMInsight text={data.ai_insight} />}

      {hasLegal && (
        <Section title="Legal identity — as the company itself discloses it">
          <div className="rounded-lg border border-edge bg-panel/40 p-3">
            <Fact label="Legal name" value={li.legal_name} source={li.legal_name_source} />
            <Fact label="Registration no." value={li.registration_no} source={li.registration_source} />
            <Fact label="Registered office" value={li.registered_office} source={li.registered_office_source} />
            <Fact label="Incorporation" value={li.incorporation} source={li.incorporation_source} />
            <Fact label="Tax id" value={li.tax_id} source={li.tax_id_source} />
            <Fact label="Address (structured data)" value={li.address_jsonld} source={li.address_source} />
            <Fact label="Founded (self-declared)" value={li.founding_date_selfdeclared} />
          </div>
        </Section>
      )}

      {regs.length > 0 && (
        <Section title="Registry & statutory identifiers found on their properties">
          <Rows
            rows={regs}
            cols={[
              { key: "kind", label: "Registry" },
              { key: "value", label: "Identifier" },
              { key: "context", label: "Where it appeared" },
              { key: "source", label: "Link" },
            ]}
          />
          <p className="mt-2 text-[11px] text-zinc-600">
            National registries (India's MCA, UK Companies House without an API key) have no open keyless API — these
            identifiers come from the company's own legally-required disclosures. Verify them on the registry portal.
          </p>
        </Section>
      )}

      {dr && Object.keys(dr).length > 0 && (
        <Section title="Domain record — the address's own registration (RDAP)">
          <div className="rounded-lg border border-edge bg-panel/40 p-3">
            <Fact label="Registrar" value={dr.registrar} />
            <Fact label="Registered" value={dr.registered} />
            <Fact label="Expires" value={dr.expires} />
            <Fact label="Status" value={(dr.status ?? []).join(", ") || null} />
            <Fact label="Nameservers" value={(dr.nameservers ?? []).join(" · ") || null} />
            {dr.queried && (
              <a href={dr.queried} target="_blank" rel="noreferrer" className="text-[11px] text-cyan-500/80 hover:text-cyan-400">
                raw RDAP record
              </a>
            )}
          </div>
        </Section>
      )}

      {edgar && Object.keys(edgar).length > 0 && (
        <Section title="US registration — SEC EDGAR (the filing regulator's own record)">
          <div className="rounded-lg border border-edge bg-panel/40 p-3">
            <Fact label="Registrant" value={edgar.name} source={edgarLink} />
            <Fact label="CIK" value={edgar.cik ? String(edgar.cik) : null} />
            <Fact label="Ticker" value={edgar.ticker} />
            <Fact label="Entity type" value={edgar.entity_type} />
            <Fact label="State of incorporation" value={edgar.state_of_incorporation} />
            <Fact label="Industry (SIC)" value={edgar.sic ? `${edgar.sic} — ${edgar.sic_description ?? ""}` : null} />
            <Fact label="Exchange" value={(edgar.exchanges ?? []).join(", ") || null} />
            <Fact label="Fiscal year end" value={edgar.fiscal_year_end} />
            <Fact label="Former names" value={(edgar.former_names ?? []).join(" · ") || null} />
            <Fact label="Addresses" value={(edgar.addresses ?? []).join(" | ") || null} />
          </div>
        </Section>
      )}

      {wd && Object.keys(wd).length > 0 && (
        <Section title="Wikidata legal facts — structured, sourced from the encyclopedia layer">
          <div className="rounded-lg border border-edge bg-panel/40 p-3">
            {Object.entries(wd).map(([k, v]) => (
              <Fact key={k} label={k.replace(/_/g, " ")} value={String(v)} />
            ))}
          </div>
        </Section>
      )}

      {(data.registry_mentions ?? []).length > 0 && (
        <Section title="Registry mentions (search layer — verify each)">
          <Rows
            rows={data.registry_mentions ?? []}
            cols={[
              { key: "title", label: "Result" },
              { key: "snippet", label: "Excerpt" },
              { key: "url", label: "Link" },
            ]}
          />
        </Section>
      )}

      {(data.coverage ?? []).length > 0 && (
        <Section title="What was actually checked (no pretending)">
          <ul className="space-y-1.5">
            {(data.coverage ?? []).map((c, i) => (
              <li key={i} className="text-xs leading-relaxed text-zinc-400">
                <span className="mr-1.5 text-emerald-500">✓</span>
                {c}
              </li>
            ))}
          </ul>
        </Section>
      )}

      {!hasLegal && regs.length === 0 && !dr && !edgar && (
        <Warn>
          No public registration identifiers surfaced for this subject. The richest path is the company's own website —
          switch to the <span className="text-amber-400">Website URL</span> input so Genesis can read its legal pages.
        </Warn>
      )}
    </div>
  );
}
