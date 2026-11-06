"use client";

import { useEffect, useMemo, useState } from "react";
import { TABS, type Report, type TabId, sectionData } from "@/lib/types";
import { downloadReport } from "@/lib/api";
import { Badge } from "@/components/ui";
import { ComplianceTab, FeaturesTab, PremortemTab, StructuralTab } from "@/components/tabs/AnalysisTabs";
import { DnaTab, FinancialTab, FrictionTab, MarketSizeTab, PricingTab, TimelineTab } from "@/components/tabs/BusinessTabs";
import { SchoolTab } from "@/components/tabs/SchoolTab";
import { MarketPerfTab } from "@/components/tabs/MarketPerfTab";
import { DeepDiveTab } from "@/components/tabs/DeepDiveTab";
import { DarkWebTab, DistributionTab, PlaybookTab, TechArchTab } from "@/components/tabs/ExecTabs";
import AdversaryTab from "@/components/tabs/AdversaryTab";
import AdvisorPanel from "@/components/AdvisorPanel";
import VerdictPanel from "@/components/VerdictPanel";

export default function ReportViewer({
  report,
  streaming,
  arrivedIds,
}: {
  report: Report;
  streaming: boolean;
  arrivedIds: readonly TabId[];
}) {
  const [active, setActive] = useState<TabId>("structural");
  const [follow, setFollow] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [exportErr, setExportErr] = useState<string | null>(null);
  const [advisorOpen, setAdvisorOpen] = useState(false);
  const [verdictOpen, setVerdictOpen] = useState(false);

  // Auto-follow the newest arriving section until the user clicks a tab.
  useEffect(() => {
    const last = arrivedIds[arrivedIds.length - 1];
    if (follow && streaming && last) {
      setActive(last);
    }
  }, [arrivedIds, follow, streaming]);

  const section = report.sections[active];
  const body = useMemo(() => {
    if (!section) return <p className="text-sm text-zinc-600">// decoding…</p>;
    switch (section.id) {
      case "structural":
        return <StructuralTab data={sectionData(section, "structural") ?? {}} />;
      case "features":
        return <FeaturesTab data={sectionData(section, "features") ?? {}} />;
      case "compliance":
        return <ComplianceTab data={sectionData(section, "compliance") ?? {}} />;
      case "premortem":
        return <PremortemTab data={sectionData(section, "premortem") ?? {}} />;
      case "timeline":
        return <TimelineTab data={sectionData(section, "timeline") ?? {}} />;
      case "pricing":
        return <PricingTab data={sectionData(section, "pricing") ?? {}} />;
      case "friction":
        return <FrictionTab data={sectionData(section, "friction") ?? {}} />;
      case "financial":
        return <FinancialTab data={sectionData(section, "financial") ?? {}} />;
      case "distribution":
        return <DistributionTab data={sectionData(section, "distribution") ?? {}} />;
      case "techarch":
        return <TechArchTab data={sectionData(section, "techarch") ?? {}} />;
      case "darkweb":
        return <DarkWebTab data={sectionData(section, "darkweb") ?? {}} />;
      case "marketsize":
        return <MarketSizeTab data={sectionData(section, "marketsize") ?? {}} />;
      case "playbook":
        return <PlaybookTab data={sectionData(section, "playbook") ?? {}} />;
      case "dna":
        return <DnaTab data={sectionData(section, "dna") ?? {}} />;
      case "school":
        return <SchoolTab data={sectionData(section, "school") ?? {}} />;
      case "markets":
        return <MarketPerfTab data={sectionData(section, "markets") ?? {}} />;
      case "deepdive":
        return <DeepDiveTab data={sectionData(section, "deepdive") ?? {}} />;
      case "adversary":
        return <AdversaryTab data={sectionData(section, "adversary") ?? {}} />;
    }
  }, [section]);

  const doExport = async (fmt: "markdown" | "zip" | "json") => {
    setExporting(true);
    setExportErr(null);
    try {
      await downloadReport(report, fmt);
    } catch {
      setExportErr("Export failed — is the backend still running? Sections can also be copied manually.");
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="flex h-full min-h-0 flex-col">
      {/* Report header */}
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-baseline gap-2">
          <h2 className="text-lg font-semibold text-zinc-100">{report.subject}</h2>
          <Badge tone="cyan">{report.sector}</Badge>
          <Badge>{report.request.mode}</Badge>
          <Badge>{report.request.geography}</Badge>
        </div>
        <div className="flex flex-col items-end gap-1">
          <div className="flex gap-2">
            <button
              onClick={() => doExport("markdown")}
              disabled={exporting}
              className="rounded border border-edge px-3 py-1.5 text-xs text-zinc-400 transition-colors hover:border-emerald-700 hover:text-emerald-400 disabled:opacity-40"
            >
              Markdown
            </button>
            <button
              onClick={() => doExport("json")}
              disabled={exporting}
              className="rounded border border-edge px-3 py-1.5 text-xs text-zinc-400 transition-colors hover:border-cyan-700 hover:text-cyan-400 disabled:opacity-40"
            >
              JSON
            </button>
            <button
              onClick={() => setVerdictOpen(true)}
              className="rounded border border-amber-800/70 bg-amber-950/20 px-3 py-1.5 text-xs font-medium text-amber-400 transition-colors hover:bg-amber-900/30"
            >
              Verdict
            </button>
            <button
              onClick={() => setAdvisorOpen(true)}
              className="rounded border border-emerald-800/70 bg-emerald-950/30 px-3 py-1.5 text-xs font-medium text-emerald-400 transition-colors hover:bg-emerald-900/30"
            >
              Ask Genesis
            </button>
            <button
              onClick={() => doExport("zip")}
              disabled={exporting}
              className="rounded border border-edge px-3 py-1.5 text-xs text-zinc-400 transition-colors hover:border-emerald-700 hover:text-emerald-400 disabled:opacity-40"
            >
              Playbook ZIP
            </button>
          </div>
          {exportErr && <p className="max-w-xs text-right text-[11px] text-red-400/90">{exportErr}</p>}
        </div>
      </div>

      {/* Tab bar */}
      <div className="flex flex-wrap gap-1 border-b border-edge pb-2">
        {TABS.map((t) => {
          const arrived = arrivedIds.includes(t.id);
          const isActive = active === t.id;
          return (
            <button
              key={t.id}
              onClick={() => {
                setFollow(false);
                setActive(t.id);
              }}
              title={t.title}
              className={`flex items-center gap-1.5 px-2.5 py-2 text-xs transition-colors duration-150 ${
                isActive ? "bg-amber-950/40 text-amber-400" : arrived ? "text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200" : "text-zinc-700"
              }`}
            >
              <span>{t.icon}</span>
              <span>{t.n}</span>
              {!arrived && <span className="h-1 w-1 animate-pulse-dot rounded-full bg-zinc-600" />}
            </button>
          );
        })}
      </div>

      {/* Section summary */}
      {section && (
        <div className="mt-3">
          <h3 className="text-sm font-medium text-zinc-200">
            {section.icon} {TABS.find((t) => t.id === active)?.title}
          </h3>
          <p className="mt-0.5 text-xs leading-relaxed text-zinc-500">{section.summary}</p>
        </div>
      )}

      {/* Section body */}
      <div className="mt-3 flex-1 overflow-y-auto pr-1">{body}</div>

      {/* Sources footer */}
      {report.sources.length > 0 && (
        <details className="mt-3 border-t border-edge pt-2">
          <summary className="cursor-pointer text-xs text-zinc-600 hover:text-zinc-400">
            {report.sources.length} evidence sources
          </summary>
          <ul className="mt-2 max-h-40 space-y-1 overflow-y-auto">
            {report.sources.map((s, i) => (
              <li key={i} className="truncate text-[11px]">
                <span className="text-zinc-600">[{s.kind}] </span>
                <a href={s.url} target="_blank" rel="noreferrer" className="text-cyan-600 hover:text-cyan-400">
                  {s.url}
                </a>
              </li>
            ))}
          </ul>
        </details>
      )}
          {verdictOpen && (
        <VerdictPanel report={report} onClose={() => setVerdictOpen(false)} />
      )}
      {advisorOpen && (
        <AdvisorPanel
          report={report}
          onClose={() => setAdvisorOpen(false)}
          onOpenTab={(id) => {
            setFollow(false);
            setActive(id);
            setAdvisorOpen(false);
          }}
        />
      )}
    </div>
  );
}
