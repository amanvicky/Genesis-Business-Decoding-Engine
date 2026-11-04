"use client";

import type { SchoolData } from "@/lib/types";
import { Badge, Card, Warn } from "@/components/ui";
import { LLMInsight, Section } from "./AnalysisTabs";

export function SchoolTab({ data }: { data: SchoolData }) {
  const gb = Object.entries(data.vocabulary?.business ?? {});
  const gp = Object.entries(data.vocabulary?.psychology ?? {});
  return (
    <div className="space-y-5">
      {data.ai_insight && <LLMInsight text={data.ai_insight} />}

      {data.sector_note && (
        <Card className="p-3">
          <p className="text-xs leading-relaxed text-zinc-400">{data.sector_note}</p>
        </Card>
      )}

      {(data.phases ?? []).map((phase) => (
        <Section key={phase.phase} title={`Phase ${phase.phase}: ${phase.name}`}>
          <p className="mb-3 text-xs leading-relaxed text-zinc-500">{phase.why}</p>
          <div className="space-y-3">
            {(phase.lessons ?? []).map((l) => (
              <Card key={l.id} className="p-4">
                <p className="text-sm font-medium text-zinc-100">{l.title}</p>
                <p className="mt-2 text-xs leading-relaxed text-zinc-300">{l.lesson}</p>

                {l.with_your_numbers && (
                  <div className="mt-3 rounded border border-emerald-900/50 bg-emerald-950/10 p-2.5">
                    <p className="text-[11px] uppercase tracking-wider text-emerald-400">with your numbers</p>
                    <p className="mt-1 text-xs leading-relaxed text-zinc-200">{l.with_your_numbers}</p>
                  </div>
                )}

                <div className="mt-3 rounded border border-red-900/40 bg-red-950/10 p-2.5">
                  <p className="text-[11px] uppercase tracking-wider text-red-400">the uncomfortable truth</p>
                  <p className="mt-1 text-xs leading-relaxed text-zinc-300">{l.truth}</p>
                </div>

                <div className="mt-2 rounded border border-edge bg-panel/60 p-2.5">
                  <p className="text-[11px] uppercase tracking-wider text-emerald-400">do this now</p>
                  <p className="mt-1 text-xs leading-relaxed text-zinc-200">{l.action}</p>
                </div>

                {(l.terms ?? []).length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {l.terms.map((t) => <Badge key={t} tone="cyan">{t}</Badge>)}
                  </div>
                )}
              </Card>
            ))}
          </div>
        </Section>
      ))}

      {(gb.length > 0 || gp.length > 0) && (
        <Section title="The vocabulary — every term, in plain words">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {gb.length > 0 && (
              <div>
                <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-amber-400">business</p>
                <ul className="space-y-1.5">
                  {gb.map(([term, def]) => (
                    <li key={term} className="text-xs leading-relaxed text-zinc-400"><span className="font-medium text-zinc-200">{term}</span> — {def}</li>
                  ))}
                </ul>
              </div>
            )}
            {gp.length > 0 && (
              <div>
                <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-cyan-400">psychology</p>
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
