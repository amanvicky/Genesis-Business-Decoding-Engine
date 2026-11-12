"use client";

import type { DarkWebData } from "@/lib/types";
import { Badge, Bullets, Card, CodeBlock, Rows, Warn } from "@/components/ui";
import { LLMInsight, Section } from "./AnalysisTabs";

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


