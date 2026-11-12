/**
 * Wire types for the Genesis pipeline.
 *
 * The console stream is a discriminated union narrowed with exhaustive
 * switches (`assertNever`); section payloads are mapped through
 * `SectionDataMap` so each tab renderer gets its own typed shape.
 */

export type Mode = "company" | "idea" | "url";
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
  "darkweb",
  "dna",
  "markets",
  "deepdive",
  "publicrecord",
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
  { id: "features", n: 2, title: "Feature Breakdown & Alternatives", icon: "▦", blurb: "shipped features with dates, the alternatives scan" },
  { id: "compliance", n: 3, title: "Jurisdictional & Regulatory Decoder", icon: "⚖", blurb: "Licenses, labor/tax law, launch-blockers" },
  { id: "premortem", n: 4, title: "Pre-Mortem & Failure Post-Mortems", icon: "☠", blurb: "Why operators like this one collapsed" },
  { id: "timeline", n: 5, title: "Genesis & Historical Timeline", icon: "◷", blurb: "Pivots, milestones, funding + revenue history" },
  { id: "pricing", n: 6, title: "Pricing — Tiers, History & Packaging Psychology", icon: "∑", blurb: "what they actually charge, as observed" },
  { id: "friction", n: 7, title: "Market Friction & Consumer Psychology", icon: "⚡", blurb: "Unvarnished complaints & demand triggers" },
  { id: "darkweb", n: 8, title: "Deep/Dark Web & Vulnerability Shield", icon: "◉", blurb: "Tor-routed lawful OSINT, breach shield" },
  { id: "dna", n: 9, title: "Product DNA — Philosophy & Psychology", icon: "☯", blurb: "why every feature exists, in plain words" },
  { id: "markets", n: 10, title: "Stock Performance — Rise & Fall", icon: "▲", blurb: "1-year chart, 52w range, the biggest rises and falls" },
  { id: "deepdive", n: 11, title: "Company Deep-Dive — What, Why, Reality & Marketing", icon: "❖", blurb: "what they do, every feature's origin story, the reality check, the marketing mechanics" },
  { id: "publicrecord", n: 12, title: "Public Record — Registration & Corporate Footprint", icon: "§", blurb: "legal identity, government registry IDs, the domain record — everything publicly filed" },
  { id: "adversary", n: 13, title: "Adversarial Red-Team Simulator", icon: "⚔", blurb: "Buyers, VCs & auditors cross-examine your plan" },
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
  readonly psychology?: readonly { driver: string; evidence: string }[];
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

export interface DnaData {
  readonly sequencing?: readonly { readonly when: string; readonly feature: string }[];
  readonly product_philosophy?: {
    readonly headline?: string;
    readonly top_patterns?: readonly { readonly name: string; readonly mentions: number; readonly philosophy: string }[];
    readonly credibility?: readonly { readonly kind: string; readonly text: string; readonly url: string }[];
  };
  readonly features?: readonly {
    readonly feature: string;
    readonly class?: string;
    readonly source?: string;
    readonly timing?: {
      readonly when: string;
      readonly year: number | null;
      readonly company_age: number | null;
      readonly stage: string | null;
      readonly why_then: string;
      readonly major_reason: string;
    };
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

export interface MarketPerfData {
  readonly traded?: boolean | null;
  readonly symbol?: string;
  readonly company_name?: string;
  readonly index?: { readonly symbol: string; readonly name: string };
  readonly currency_display?: string;
  readonly performance?: {
    readonly current?: number;
    readonly change_1y_pct?: number;
    readonly high_52w?: { readonly price: number; readonly date: string };
    readonly low_52w?: { readonly price: number; readonly date: string };
    readonly ytd_pct?: number;
    readonly max_drawdown?: { readonly pct: number; readonly date: string };
    readonly best_weeks?: readonly { readonly date: string; readonly change_pct: number; readonly from: number; readonly to: number }[];
    readonly worst_weeks?: readonly { readonly date: string; readonly change_pct: number; readonly from: number; readonly to: number }[];
    readonly series?: readonly { readonly date: string; readonly close: number }[];
  };
  readonly sparkline?: readonly number[];
  readonly summary?: string;
  readonly note?: string;
  readonly ai_insight?: string;
}

export interface DeepDiveData {
  readonly subject?: string;
  readonly mode?: string;
  readonly what_they_do?: {
    readonly the_problem?: string;
    readonly the_problem_in_user_words?: readonly {
      readonly quote: string;
      readonly source: string;
      readonly url?: string | null;
    }[];
    readonly the_solution?: string;
    readonly the_trigger?: string;
    readonly founder_logic?: string;
  };
  readonly feature_inventory?: readonly {
    readonly feature: string;
    readonly kind?: string;
    readonly what_it_does?: string;
    readonly the_issue_before?: string;
    readonly the_trigger?: string;
    readonly the_impact?: string;
    readonly psych_basis?: readonly string[];
    readonly evolution?: string | null;
  }[];
  readonly product_milestones?: readonly {
    readonly what: string;
    readonly when: string;
    readonly url?: string | null;
  }[];
  readonly reality_check?: {
    readonly items?: readonly { readonly area: string; readonly what: string }[];
  };
  readonly marketing?: {
    readonly mechanics?: readonly {
      readonly mechanic: string;
      readonly signals?: readonly string[];
      readonly dna_confirmed?: boolean;
      readonly how_they_used_it?: string;
      readonly evidence_url?: string | null;
      readonly what_they_promote?: string;
      readonly psych?: string;
    }[];
    readonly the_hook?: string;
    readonly current_push?: readonly string[];
    readonly channel_ranking?: readonly string[];
    readonly note?: string;
  };
  readonly note?: string;
  readonly ai_insight?: string;
}

export interface RegistryRow {
  readonly kind?: string;
  readonly value?: string;
  readonly context?: string;
  readonly source?: string;
}

export interface PublicRecordData {
  readonly mode?: string;
  readonly domain?: string;
  readonly site?: {
    readonly url?: string;
    readonly title?: string;
    readonly description?: string;
    readonly tech?: readonly string[];
    readonly socials?: Readonly<Record<string, string>>;
    readonly emails?: readonly string[];
    readonly phones?: readonly string[];
  } | null;
  readonly legal_identity?: {
    readonly legal_name?: string;
    readonly legal_name_source?: string;
    readonly registration_no?: string;
    readonly registration_kind?: string;
    readonly registration_source?: string;
    readonly registered_office?: string;
    readonly registered_office_source?: string;
    readonly incorporation?: string;
    readonly incorporation_source?: string;
    readonly tax_id?: string;
    readonly tax_id_kind?: string;
    readonly tax_id_source?: string;
    readonly address_jsonld?: string;
    readonly address_source?: string;
    readonly founding_date_selfdeclared?: string;
  };
  readonly registrations?: readonly RegistryRow[];
  readonly domain_record?: {
    readonly registrar?: string;
    readonly registered?: string;
    readonly expires?: string;
    readonly last_changed?: string;
    readonly status?: readonly string[];
    readonly nameservers?: readonly string[];
    readonly queried?: string;
  } | null;
  readonly edgar?: {
    readonly cik?: number;
    readonly name?: string;
    readonly ticker?: string;
    readonly entity_type?: string;
    readonly state_of_incorporation?: string;
    readonly sic?: string;
    readonly sic_description?: string;
    readonly exchanges?: readonly string[];
    readonly fiscal_year_end?: string;
    readonly former_names?: readonly string[];
    readonly addresses?: readonly string[];
  } | null;
  readonly wikidata?: Readonly<Record<string, string>> | null;
  readonly registry_mentions?: readonly { readonly title?: string; readonly snippet?: string; readonly url?: string }[];
  readonly coverage?: readonly string[];
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
  darkweb: DarkWebData;
  dna: DnaData;
  markets: MarketPerfData;
  deepdive: DeepDiveData;
  publicrecord: PublicRecordData;
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
  | { type: "saved"; brief_id: string; subject: string } // the vault stored this decode (powers the watch button)
  | { type: "error"; msg: string };

export function assertNever(value: never): never {
  throw new Error(`unhandled variant: ${JSON.stringify(value)}`);
}

/** Runtime-safe typed accessor for JSON section payloads. */
export function sectionData<K extends TabId>(section: Section | undefined, id: K): SectionData<K> | null {
  if (!section || section.id !== id) return null;
  return section.data as unknown as SectionData<K>;
}

/* ---------------------------------------------------- battle · vault · watch */

export type BattleKind = "idea" | "company" | "url";

export interface BattleItem {
  kind: BattleKind;
  text: string;
}

export interface BattleRequest {
  items: BattleItem[];
  geography: Geography;
  context?: string;
  team_size: number;
  runway_target_months: number;
  include_darkweb: boolean;
}

export interface BattleGates {
  readonly pass: number;
  readonly caution: number;
  readonly fail: number;
  readonly pending: number;
}

export interface BattleRow {
  readonly i: number;
  readonly label: string;
  readonly kind: BattleKind;
  readonly subject: string;
  readonly score: number | null;
  readonly decision: string;
  readonly fatals: number | null;
  readonly criticals: number | null;
  readonly gates: BattleGates;
  readonly brief_id?: string;
}

export interface BattleResult {
  readonly rows: readonly BattleRow[];
  readonly winner: number | null; // null = the matrix tied → PENDING, never a coin flip
  readonly prose: string;
  readonly llm_wrote_prose: boolean;
}

export type BattleEvent =
  | { type: "battle_start"; ideas: string[]; kinds: string[] }
  | { type: "idea_start"; i: number; subject: string; kind: string }
  | { type: "idea_done"; i: number; subject: string; kind?: string; brief_id?: string; decision?: string; score?: number | null }
  | { type: "battle_done"; rows: BattleRow[]; winner: number | null; prose: string; llm_wrote_prose: boolean }
  | { type: "log"; level: LogLevel; agent: string; msg: string }
  | { type: "status"; step: number; agent: string; state: AgentState; title: string; ms?: number }
  | { type: "error"; msg: string };

export interface BriefMeta {
  readonly id: string;
  readonly subject: string;
  readonly mode: Mode;
  readonly created_at: string;
  readonly watched: boolean;
  readonly watch_days: number;
  readonly last_checked: string | null;
  readonly checks: number;
  readonly battle: boolean;
}

export interface DriftRow {
  readonly field: string;
  readonly label: string;
  readonly tab: string;
  readonly kind: string;
  readonly action: string;
  readonly old: string;
  readonly new: string;
}

export interface DriftAlert {
  readonly id: string;
  readonly brief_id: string;
  readonly subject: string;
  readonly at: string;
  readonly seen: boolean;
  readonly rows: readonly DriftRow[];
}

export interface WatchStatus {
  readonly running: boolean;
  readonly done: number;
  readonly total: number;
  readonly current: string;
  readonly watched_count: number;
  readonly last_run: string | null;
  readonly drifts: readonly DriftAlert[];
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
