import {
  type AdviceEvent,
  type AnalyzeRequest,
  type BattleEvent,
  type BattleRequest,
  type BriefMeta,
  type ConsoleEvent,
  type LogLevel,
  type Report,
  type VerdictMemo,
  type WatchStatus,
  assertNever,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

/** Compile-time-checked route literals for the backend surface. */
export type ApiRoute =
  | `/api/${"health" | "analyze/stream" | "battle/stream" | "advise/stream" | "briefs" | "briefs/watch" | "watch/status" | "watch/check" | "watch/ack"}`
  | `/api/export/${"markdown" | "zip" | "json"}`;

const url = (route: ApiRoute) => `${API_URL}${route}`;

export interface HealthInfo {
  status: string;
  version: string;
  offline_mode: boolean;
  tor: { available: boolean; reason?: string; exit_ip?: string };
  llm: { available: boolean; model: string | null };
}

export async function fetchHealth(): Promise<HealthInfo | null> {
  try {
    const res = await fetch(url("/api/health"), { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as HealthInfo;
  } catch {
    return null;
  }
}

/**
 * POST + consume an NDJSON event stream over XHR, invoking `onEvent` for
 * every parsed line. XHR (onprogress) is the transport whose end-to-end
 * delivery of the long battle streams is proven; every event of every run
 * arrived in the same browser where the earlier reader-based loop's
 * completion was unverifiable.
 */
function streamNdjson<TParsed>(
    route: ApiRoute,
    body: unknown,
    parse: (line: string) => TParsed,
    onEvent: (ev: TParsed) => void,
    badEventLabel: string,
    signal?: AbortSignal,
): Promise<void> {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open("POST", url(route), true);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.timeout = 0; // a battle can run past ten minutes; liveness is the stream itself
        let seen = 0;
        let buffer = "";
        const pump = () => {
            const text = xhr.responseText;
            if (text.length <= seen) return;
            buffer += text.slice(seen);
            seen = text.length;
            let nl: number;
            while ((nl = buffer.indexOf("\n")) !== -1) {
                const line = buffer.slice(0, nl).trim();
                buffer = buffer.slice(nl + 1);
                if (!line) continue;
                try {
                    onEvent(parse(line));
                } catch (err) {
                    console.error(badEventLabel, err, line.slice(0, 200));
                }
            }
        };
        xhr.onprogress = pump;
        xhr.onload = () => {
            pump();
            if (xhr.status >= 200 && xhr.status < 300) resolve();
            else reject(new Error(`backend returned ${xhr.status}`));
        };
        xhr.onerror = () => reject(new Error("backend unreachable — is it up?"));
        xhr.ontimeout = () => reject(new Error("backend stream timed out"));
        xhr.onabort = () => resolve();
        signal?.addEventListener("abort", () => xhr.abort(), { once: true });
        xhr.send(JSON.stringify(body));
    });
}

/**
 * POST the analysis request and consume the NDJSON event stream,
 * invoking `onEvent` for every parsed console event.
 */
export async function streamAnalysis(
  req: AnalyzeRequest,
  onEvent: (ev: ConsoleEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  return streamNdjson("/api/analyze/stream", req, parseEvent, onEvent, "bad event", signal);
}

const LEVELS: readonly LogLevel[] = ["info", "warn", "error", "success", "agent"];

function parseEvent(line: string): ConsoleEvent {
  const raw: Record<string, unknown> = JSON.parse(line);
  switch (raw["type"]) {
    case "log":
      return {
        type: "log",
        level: LEVELS.includes(raw["level"] as LogLevel) ? (raw["level"] as LogLevel) : "info",
        agent: String(raw["agent"] ?? "?"),
        msg: String(raw["msg"] ?? ""),
      };
    case "status":
      return {
        type: "status",
        step: Number(raw["step"] ?? 0),
        agent: String(raw["agent"] ?? "?"),
        state: raw["state"] === "done" || raw["state"] === "failed" ? raw["state"] : "running",
        title: String(raw["title"] ?? ""),
        ms: raw["ms"] === undefined ? undefined : Number(raw["ms"]),
      };
    case "section": {
      const section = raw["section"] as ConsoleEvent extends { type: "section"; section: infer S } ? S : never;
      return { type: "section", section };
    }
    case "done":
        return { type: "done", report: raw["report"] as Report };
    case "saved":
        return { type: "saved", brief_id: String(raw["brief_id"] ?? ""), subject: String(raw["subject"] ?? "") };
    case "error":
        return { type: "error", msg: String(raw["msg"] ?? "unknown backend error") };
    default:
        return assertNever(raw as never);
  }
}

/** Download the report as Markdown, structured JSON, or the report ZIP. */
export async function downloadReport(report: Report, fmt: "markdown" | "zip" | "json"): Promise<void> {
  const res = await fetch(url(`/api/export/${fmt}`), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(report),
  });
  if (!res.ok) throw new Error(`export failed: ${res.status}`);
  const blob = await res.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  const subject = report.subject.replace(/[^\w-]+/g, "_").slice(0, 40) || "genesis";
  const ext = fmt === "zip" ? "zip" : fmt === "json" ? "json" : "md";
  a.download = `GENESIS_${subject}.${ext}`;
  a.click();
  URL.revokeObjectURL(a.href);
}

/** Stream the real-time advisor: reasoning trail, then the grounded answer. */
export async function streamAdvice(
  question: string,
  report: Report,
  onEvent: (ev: AdviceEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  return streamNdjson(
    "/api/advise/stream",
    { question, report },
    (line) => JSON.parse(line) as AdviceEvent,
    onEvent,
    "bad advice event",
    signal,
  );
}

/** The Verdict Protocol: brief + FMF answers → deterministic decision memo. */
export async function requestVerdict(report: Report, fmfAnswers: boolean[]): Promise<VerdictMemo> {
    const res = await fetch(url("/api/verdict" as ApiRoute), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ report, fmf_answers: fmfAnswers }),
    });
    if (!res.ok) {
        throw new Error(`verdict failed: ${res.status}`);
    }
    return (await res.json()) as VerdictMemo;
}

/* ---------------------------------------------------- battle · vault · watch */

/** Stream an Idea Battle: logs per idea, then the matrix + rule-based winner. */
export async function streamBattle(
    req: BattleRequest,
    onEvent: (ev: BattleEvent) => void,
    signal?: AbortSignal,
): Promise<void> {
    return streamNdjson("/api/battle/stream", req, parseBattleEvent, onEvent, "bad battle event", signal);
}

const BATTLE_LEVELS = LEVELS;

function parseBattleEvent(line: string): BattleEvent {
    const raw: Record<string, unknown> = JSON.parse(line);
    switch (raw["type"]) {
        case "battle_start":
            return { type: "battle_start", ideas: (raw["ideas"] as string[]) ?? [], kinds: (raw["kinds"] as string[]) ?? [] };
        case "idea_start":
            return { type: "idea_start", i: Number(raw["i"] ?? 0), subject: String(raw["subject"] ?? ""), kind: String(raw["kind"] ?? "idea") };
        case "idea_done":
            return {
                type: "idea_done",
                i: Number(raw["i"] ?? 0),
                subject: String(raw["subject"] ?? ""),
                kind: raw["kind"] === undefined ? undefined : String(raw["kind"]),
                brief_id: raw["brief_id"] === undefined ? undefined : String(raw["brief_id"]),
                decision: raw["decision"] === undefined ? undefined : String(raw["decision"]),
                score: raw["score"] === undefined ? undefined : Number(raw["score"]),
            };
        case "battle_done":
            return {
                type: "battle_done",
                rows: (raw["rows"] as BattleEvent extends { type: "battle_done"; rows: infer R } ? R : never) ?? [],
                winner: raw["winner"] === null || raw["winner"] === undefined ? null : Number(raw["winner"]),
                prose: String(raw["prose"] ?? ""),
                llm_wrote_prose: Boolean(raw["llm_wrote_prose"]),
            };
        case "log":
            return {
                type: "log",
                level: BATTLE_LEVELS.includes(raw["level"] as LogLevel) ? (raw["level"] as LogLevel) : "info",
                agent: String(raw["agent"] ?? "?"),
                msg: String(raw["msg"] ?? ""),
            };
        case "status":
            return {
                type: "status",
                step: Number(raw["step"] ?? 0),
                agent: String(raw["agent"] ?? "?"),
                state: raw["state"] === "done" || raw["state"] === "failed" ? raw["state"] : "running",
                title: String(raw["title"] ?? ""),
                ms: raw["ms"] === undefined ? undefined : Number(raw["ms"]),
            };
        case "error":
            return { type: "error", msg: String(raw["msg"] ?? "unknown backend error") };
        default:
            return assertNever(raw as never);
    }
}

/** The vault: every stored decode, newest first (metadata only). */
export async function fetchBriefs(): Promise<BriefMeta[]> {
    try {
        const res = await fetch(url("/api/briefs"), { cache: "no-store" });
        if (!res.ok) return [];
        const body = (await res.json()) as { briefs: BriefMeta[] };
        return body.briefs ?? [];
    } catch {
        return [];
    }
}

/** Mark a stored brief watched — the dashboard re-decodes it every `days`. */
export async function markWatched(briefId: string, days = 7): Promise<boolean> {
    const res = await fetch(url("/api/briefs/watch"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ brief_id: briefId, days }),
    });
    return res.ok;
}

/** Drift chip data + live checker progress. Null when the API is unreachable. */
export async function fetchWatchStatus(): Promise<WatchStatus | null> {
    try {
        const res = await fetch(url("/api/watch/status"), { cache: "no-store" });
        if (!res.ok) return null;
        return (await res.json()) as WatchStatus;
    } catch {
        return null;
    }
}

/** Lazy trigger (dashboard-open): re-decode what's due, in the background. */
export async function triggerWatchCheck(): Promise<void> {
    try {
        await fetch(url("/api/watch/check"), { cache: "no-store" });
    } catch {
        // the dashboard works fine without the watch layer
    }
}

/** Mark every stored drift alert as seen. */
export async function ackWatchDrifts(): Promise<boolean> {
    try {
        const res = await fetch(url("/api/watch/ack"), { method: "POST" });
        return res.ok;
    } catch {
        return false;
    }
}
