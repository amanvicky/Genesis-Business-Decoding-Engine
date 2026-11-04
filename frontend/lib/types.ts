/**
 * Wire types for the Genesis pipeline.
 *
 * The console stream is a discriminated union narrowed with exhaustive
 * switches (`assertNever`); section payloads are mapped through
 * `SectionDataMap` so each tab renderer gets its own typed shape.
 */

export type Mode = "company" | "idea";
export type Geography = "india" | "us" | "global";

export interface AnalyzeRequest {
  mode: Mode;
  query: string;
  geography: Geography;
  context?: string;
  team_size: number;
  runway_target_months: number;
  include_darkweb: boolean;
}

/* ------------------------------------------------------------------ tabs */

export const TAB_IDS = [
  "structural",
  "features",
  "compliance",
  "premortem",
  "timeline",
  "pricing",
  "friction",
  "financial",
  "distribution",
  "techarch",
  "darkweb",
  "playbook",
  "marketsize",
  "dna",
  "school",
  "adversary",
] as const;

export type TabId = (typeof TAB_IDS)[number];

export interface TabDef {
  readonly id: TabId;
  readonly n: number;
  readonly title: string;
  readonly icon: string;
  readonly blurb: string;
}

export const TABS = [
  { id: "structural", n: 1, title: "Structural Feasibility & Core Mechanics", icon: "◈", blurb: "Pain validation, timing shifts, systemic moats" },
  { id: "features", n: 2, title: "Feature Breakdown & MVP Sequencing", icon: "▦", blurb: "Day-1 wedge vs enterprise bloat, build order" },
  { id: "compliance", n: 3, title: "Jurisdictional & Regulatory Decoder", icon: "⚖", blurb: "Licenses, labor/tax law, launch-blockers" },
  { id: "premortem", n: 4, title: "Pre-Mortem & Failure Post-Mortems", icon: "☠", blurb: "Why operators like this one collapsed" },
  { id: "timeline", n: 5, title: "Genesis & Historical Timeline", icon: "◷", blurb: "Pivots, milestones, funding events" },
  { id: "pricing", n: 6, title: "Pricing & Unit Economics", icon: "∑", blurb: "Tier math, margins, LTV:CAC, psychology" },
  { id: "friction", n: 7, title: "Market Friction & Consumer Psychology", icon: "⚡", blurb: "Unvarnished complaints & demand triggers" },
  { id: "financial", n: 8, title: "Financial Reality & Burn Calculator", icon: "▮", blurb: "Runway math with zero sugarcoating" },
  { id: "distribution", n: 9, title: "Unfair Distribution Channels", icon: "⇄", blurb: "Zero-cost loops, organic acquisition" },
  { id: "techarch", n: 10, title: "Technical Architecture & Scaffolding", icon: "⌘", blurb: "Stack decisions + starter code files" },
  { id: "darkweb", n: 11, title: "Deep/Dark Web & Vulnerability Shield", icon: "◉", blurb: "Tor-routed lawful OSINT, breach shield" },
  { id: "playbook", n: 12, title: "The Systematic Execution Playbook", icon: "➤", blurb: "Phased sequencing, KYC friction, scaling" },
  { id: "marketsize", n: 13, title: "Market Sizing & Capital Strategy", icon: "◎", blurb: "TAM/SAM/SOM math, raise vs bootstrap, founder fit" },
  { id: "dna", n: 14, title: "Product DNA — Philosophy & Psychology", icon: "☯", blurb: "why every feature exists, in plain words" },
  { id: "school", n: 15, title: "Founder School — The Knowledge Transfer", icon: "✦", blurb: "the zero-to-one curriculum, taught with your own numbers" },
  { id: "adversary", n: 16, title: "Adversarial Red-Team Simulator", icon: "⚔", blurb: "Buyers, VCs & auditors cross-examine your plan" },
] as const satisfies readonly TabDef[];

/* ---------------------------------------------------- section data shapes */

export interface EvidenceVolume {
  readonly search_results?: number;
  readonly hn_stories?: number;
  readonly reddit_posts?: number;
  readonly review_snippets?: number;
}

export interface StructuralData {
  readonly verdict?: string;
  readonly verdict_score?: number;
  readonly mode?: string;
  readonly pain_points?: readonly Voice[];
  readonly demand_triggers?: readonly Voice[];
  readonly core_mechanics?: readonly string[];
  readonly moats?: readonly { type: string; strength: string; evidence: string }[];
  readonly timing_shifts?: readonly { shift: string; implication: string }[];
  readonly keyphrases?: readonly string[];
  readonly evidence_volume?: EvidenceVolume;
  readonly ai_insight?: string;
}

export interface Voice {
  readonly source?: string;
  readonly text?: string;
  readonly url?: string;
}

export interface FieldReport {
  readonly title?: string;
  readonly snippet?: string;
  readonly url?: string;
}

export interface FeatureRow {
  readonly date?: string;
  readonly feature?: string;
  readonly detail?: string;
  readonly source?: string;
  readonly url?: string;
  readonly klass?: string;
  readonly class?: string;
}

export interface RoadmapItem {
  readonly feature?: string;
  readonly why?: string;
  readonly source?: string;
  readonly gate?: string;
}

export interface BinaryRoadmap {
  readonly build_now?: readonly RoadmapItem[];
  readonly build_later?: readonly RoadmapItem[];
  readonly never_for_mvp?: readonly RoadmapItem[];
}

export interface AlternativesScan {
  readonly candidates?: readonly string[];
  readonly chatter?: readonly { readonly text: string; readonly url: string }[];
}

export interface FeaturesData {
  readonly founded_year?: number | null;
  readonly feature_count?: number;
  readonly class_counts?: Readonly<Record<string, number>>;
  readonly features?: readonly FeatureRow[];
  readonly binary_roadmap?: BinaryRoadmap;
  readonly usp_candidates?: readonly { phrase: string; mentions: number }[];
  readonly true_usp?: string;
  readonly mvp_sequence?: readonly { order: number; build: string }[];
  readonly alternatives?: AlternativesScan;
  readonly ai_insight?: string;
}

export interface ComplianceItem {
  readonly item?: string;
  readonly why?: string;
  readonly cost?: string;
  readonly time?: string;
  readonly severity?: string;
}

export interface ComplianceData {
  readonly sector_detected?: string;
  readonly jurisdictions?: { us?: boolean; india?: boolean };
  readonly landmines?: readonly ComplianceItem[];
  readonly critical_count?: number;
  readonly us_state_matrix?: readonly { state: string; burden: string; severity: string; notes: string }[];
  readonly us_payroll_matrix?: readonly {
    state: string;
    income_tax: string;
    sui_new: string;
    sdi: string;
    paid_leave: string;
    final_pay: string;
    local_taxes: boolean;
    gotcha: string;
  }[];
  readonly us_expansion_order?: readonly { state: string; why: string }[];
  readonly india_state_notes?: readonly { state: string; note: string }[];
  readonly checklist?: readonly { order: number; item: string; cost: string; time: string }[];
  readonly disclaimer?: string;
  readonly ai_insight?: string;
}

export interface FailureAnalog {
  readonly name?: string;
  readonly domain?: string;
  readonly years?: string;
  readonly what_happened?: string;
  readonly root_cause?: string;
  readonly operational_flaw?: string;
  readonly lesson?: string;
}

export interface PremortemData {
  readonly analogs?: readonly FailureAnalog[];
  readonly field_reports?: readonly FieldReport[];
  readonly common_failure_modes?: readonly { mode: string; analogs_affected: number; counter: string }[];
  readonly premortem_questions?: readonly string[];
  readonly ai_insight?: string;
}

export interface TimelineData {
  readonly mode?: string;
  readonly founded_year?: number | null;
  readonly events?: readonly { year: string; event: string; pivot?: boolean; date?: string }[];
  readonly pivots?: readonly { year: string; event: string }[];
  readonly funding_events?: readonly { amount: string; context: string }[];
  readonly gates?: readonly { gate: string; exit_criteria: string; artifacts: readonly string[] }[];
  readonly note?: string;
  readonly ai_insight?: string;
}

export interface PricingTier {
  readonly name?: string;
  readonly price?: string;
  readonly context?: string;
}

export interface PricingData {
  readonly tiers?: readonly PricingTier[];
  readonly history?: readonly { date: string; snapshot: string; prices: readonly { raw: string; context: string }[] }[];
  readonly sandbox?: { opex_month?: number };
  readonly unit_economics?: {
    arpa?: number;
    currency?: string;
    assumed_gross_margin?: number;
    margin_basis?: string;
    avg_lifetime_months?: number;
    ltv?: number;
    cac_organic_proxy?: number;
    ltv_cac_ratio?: number;
    cac_payback_months?: number;
    formulas?: readonly string[];
  };
  readonly psychology?: readonly { driver: string; evidence: string }[];
  readonly recommendation?: readonly string[];
  readonly ai_insight?: string;
}

export interface FrictionData {
  readonly voice_count?: number;
  readonly complaint_clusters?: readonly { cluster: string; count: number; share: string }[];
  readonly representative_voices?: readonly (Voice & { cluster?: string })[];
  readonly demand_triggers?: readonly (Voice & { trigger?: string })[];
  readonly trigger_summary?: readonly { trigger: string; count: number }[];
  readonly caveat?: string;
  readonly ai_insight?: string;
}

export interface FinancialData {
  readonly currency?: string;
  readonly team_size?: number;
  readonly salary_engineer_loaded?: number;
  readonly salary_founder_draw?: number;
  readonly infra_month?: number;
  readonly tools_month?: number;
  readonly legal_year?: number;
  readonly runway_target_months?: number;
  readonly computed?: {
    payroll_month?: number;
    burn_month?: number;
    capital_needed?: number;
    breakeven_customers?: number;
    arpa_assumption?: number;
    gross_margin_assumption?: number;
  };
  readonly sensitivity?: readonly { scenario: string; burn_delta: number }[];
  readonly warnings?: readonly string[];
  readonly formulas?: Readonly<Record<string, string>>;
  readonly ai_insight?: string;
}

export interface DistributionChannel {
  readonly name?: string;
  readonly loop?: string;
  readonly effort?: string;
  readonly time_to_first_signal?: string;
  readonly actions?: readonly string[];
  readonly corpus_signal?: number;
}

export interface DistributionData {
  readonly channels?: readonly DistributionChannel[];
  readonly strategy?: readonly string[];
  readonly ai_insight?: string;
}

export interface ScaffoldFile {
  readonly path?: string;
  readonly language?: string;
  readonly content?: string;
}

export interface TechArchData {
  readonly stack?: readonly string[];
  readonly architecture?: Readonly<Record<string, string>>;
  readonly decisions?: readonly { decision: string; why: string }[];
  readonly files?: readonly ScaffoldFile[];
  readonly ai_insight?: string;
}

export interface DarkWebData {
  readonly skipped?: boolean;
  readonly reason?: string;
  readonly tor?: { available?: boolean; reason?: string; exit_ip?: string; proxy?: string };
  readonly findings?: readonly { source: string; title: string; url: string; snippet: string; risk: string }[];
  readonly breaches?: readonly { name: string; date: string; accounts: number; data_classes: readonly string[]; description: string }[];
  readonly guidance?: readonly string[];
  readonly ethics_notice?: string;
  readonly ai_insight?: string;
}

export interface PlaybookData {
  readonly phases?: readonly { phase: string; steps: readonly ({ action?: string; cost?: string; window?: string; step?: string; friction?: string; fix?: string; time?: string; hurdle?: string; strategy?: string } | string)[]; hurdle?: string }[];
  readonly kyc_docs?: readonly string[];
  readonly kill_criteria?: readonly string[];
  readonly note?: string;
  readonly ai_insight?: string;
}

export interface AdversaryChallenge {
  readonly severity?: string;
  readonly question?: string;
  readonly why_fatal?: string;
  readonly triggered_by?: string;
  readonly passing_answer?: string;
}

export interface AdversaryPersona {
  readonly persona?: string;
  readonly role?: string;
  readonly stance?: string;
  readonly verdict?: string;
  readonly kills?: readonly AdversaryChallenge[];
}

export interface AdversaryData {
  readonly fatal_count?: number;
  readonly serious_count?: number;
  readonly personas?: readonly AdversaryPersona[];
  readonly overall_verdict?: string;
  readonly protocol?: readonly string[];
  readonly identity?: Readonly<Record<string, unknown>>;
  readonly ai_insight?: string;
}

export interface MarketSizeData {
  readonly market_base?: {
    readonly buying_units?: number;
    readonly unit?: string;
    readonly basis?: string;
    readonly sector?: string;
    readonly geography?: string;
  };
  readonly assumptions?: { readonly arpa?: number; readonly currency?: string; readonly arpa_source?: string };
  readonly tam?: { readonly value?: number; readonly display?: string; readonly basis?: string };
  readonly sam?: { readonly value?: number; readonly display?: string; readonly basis?: string };
  readonly som_by_year?: readonly {
    readonly year: string;
    readonly customers: number;
    readonly value: number;
    readonly display: string;
    readonly adoption: string;
  }[];
  readonly formulas?: readonly string[];
  readonly verdict?: string;
  readonly verdict_tone?: "green" | "amber" | "red";
  readonly capital_strategy?: {
    readonly recommended_raise?: number | null;
    readonly raise_formula?: string;
    readonly raise_when?: string;
    readonly dilution_at_geo_cap_pct?: number | null;
    readonly dilution_formula?: string;
    readonly geo_norms?: { readonly pre_seed_cap_usd?: number; readonly seed_valuation_usd?: number; readonly note?: string };
    readonly bootstrap_note?: string;
  };
  readonly founder_market_fit?: {
    readonly instruction?: string;
    readonly questions?: readonly { readonly q: string; readonly weight: string; readonly invert?: boolean }[];
  };
  readonly investor_question_map?: readonly { readonly question: string; readonly answered_by: string }[];
  readonly evidence_money_signals?: readonly { readonly raw: string; readonly context: string }[];
  readonly note?: string;
  readonly ai_insight?: string;
}

export interface DnaData {
  readonly product_philosophy?: {
    readonly headline?: string;
    readonly top_patterns?: readonly { readonly name: string; readonly mentions: number; readonly philosophy: string }[];
    readonly credibility?: readonly { readonly kind: string; readonly text: string; readonly url: string }[];
  };
  readonly features?: readonly {
    readonly feature: string;
    readonly class?: string;
    readonly source?: string;
    readonly patterns: readonly {
      readonly name: string;
      readonly philosophy: string;
      readonly psychology: readonly { readonly principle: string; readonly explained: string }[];
      readonly business: string;
      readonly refine: string;
      readonly worked?: string;
      readonly played_out?: readonly { readonly kind: string; readonly text: string; readonly url: string }[];
    }[];
  }[];
  readonly idea_lens?: {
    readonly sector: string;
    readonly recommended: readonly {
      readonly name: string;
      readonly philosophy: string;
      readonly psychology: readonly { readonly principle: string; readonly explained: string }[];
      readonly business: string;
      readonly refine: string;
      readonly worked?: string;
    }[];
    readonly note: string;
  };
  readonly glossary_business?: Readonly<Record<string, string>>;
  readonly glossary_psych?: Readonly<Record<string, string>>;
  readonly note?: string;
  readonly ai_insight?: string;
}

export interface SchoolData {
  readonly phases?: readonly {
    readonly phase: number;
    readonly name: string;
    readonly why: string;
    readonly lessons: readonly {
      readonly id: string;
      readonly title: string;
      readonly lesson: string;
      readonly truth: string;
      readonly action: string;
      readonly terms: readonly string[];
      readonly with_your_numbers?: string;
    }[];
  }[];
  readonly vocabulary?: {
    readonly business?: Readonly<Record<string, string>>;
    readonly psychology?: Readonly<Record<string, string>>;
  };
  readonly sector_note?: string;
  readonly note?: string;
  readonly ai_insight?: string;
}

/** TabId → its data shape. The single source of truth for renderers. */
export interface SectionDataMap {
  structural: StructuralData;
  features: FeaturesData;
  compliance: ComplianceData;
  premortem: PremortemData;
  timeline: TimelineData;
  pricing: PricingData;
  friction: FrictionData;
  financial: FinancialData;
  distribution: DistributionData;
  techarch: TechArchData;
  darkweb: DarkWebData;
  playbook: PlaybookData;
  marketsize: MarketSizeData;
  dna: DnaData;
  school: SchoolData;
  adversary: AdversaryData;
}

export type SectionData<K extends TabId = TabId> = SectionDataMap[K];

export interface Section<K extends TabId = TabId> {
  readonly id: K;
  readonly title: string;
  readonly icon: string;
  readonly summary: string;
  readonly data: SectionData<K>;
}

export interface SourceRef {
  readonly url: string;
  readonly kind: string;
  readonly title: string;
}

export interface Report {
  readonly request: AnalyzeRequest;
  readonly subject: string;
  readonly sector: string;
  readonly generated_at: string;
  readonly sections: Readonly<Partial<Record<TabId, Section>>>;
  readonly sources: readonly SourceRef[];
}

/* -------------------------------------------------------- console stream */

export type LogLevel = "info" | "warn" | "error" | "success" | "agent";
export type AgentState = "running" | "done" | "failed";

export type ConsoleEvent =
  | { type: "log"; level: LogLevel; agent: string; msg: string }
  | { type: "status"; step: number; agent: string; state: AgentState; title: string; ms?: number }
  | { type: "section"; section: Section }
  | { type: "done"; report: Report }
  | { type: "error"; msg: string };

export function assertNever(value: never): never {
  throw new Error(`unhandled variant: ${JSON.stringify(value)}`);
}

/** Runtime-safe typed accessor for JSON section payloads. */
export function sectionData<K extends TabId>(section: Section | undefined, id: K): SectionData<K> | null {
  if (!section || section.id !== id) return null;
  return section.data as unknown as SectionData<K>;
}

/* ------------------------------------------------------------- advisor */

export interface AdviceEvent {
  readonly type: "log" | "answer" | "error";
  readonly msg?: string;
  readonly answer?: string;
  readonly bullets?: readonly string[];
  readonly open_tabs?: readonly TabId[];
  readonly followups?: readonly string[];
}

/* -------------------------------------------------------------- verdict */

export interface VerdictMemo {
  readonly subject: string;
  readonly decision: "GO" | "NO-GO" | "CONDITIONAL" | "PENDING";
  readonly rationale: string;
  readonly gates: readonly {
    readonly name: string;
    readonly status: "pass" | "caution" | "fail" | "pending";
    readonly basis: string;
    readonly fix: string;
  }[];
  readonly founder_market_fit: {
    readonly score: number | null;
    readonly total: number;
    readonly rows: readonly { readonly q: string; readonly weight: string; readonly answer: boolean | null; readonly good: boolean | null }[];
  };
  readonly conditions: readonly string[];
  readonly next_actions: readonly string[];
  readonly generated_at: string;
  readonly protocol_version: number;
}
