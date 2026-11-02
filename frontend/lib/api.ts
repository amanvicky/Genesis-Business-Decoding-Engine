import {
  type AnalyzeRequest,
  type ConsoleEvent,
  type LogLevel,
  type Report,
  assertNever,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

/** Compile-time-checked route literals for the backend surface. */
export type ApiRoute = `/api/${"health" | "analyze/stream" | `export/${"markdown" | "zip" | "json"}`}`;

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
 * POST the analysis request and consume the NDJSON event stream,
 * invoking `onEvent` for every parsed console event.
 */
export async function streamAnalysis(
  req: AnalyzeRequest,
  onEvent: (ev: ConsoleEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(url("/api/analyze/stream"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
    signal,
  });
  if (!res.ok || !res.body) {
    throw new Error(`backend returned ${res.status}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let nl: number;
    while ((nl = buffer.indexOf("\n")) !== -1) {
      const line = buffer.slice(0, nl).trim();
      buffer = buffer.slice(nl + 1);
      if (!line) continue;
      try {
        onEvent(parseEvent(line));
      } catch (err) {
        console.error("bad event", err, line.slice(0, 200));
      }
    }
  }
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
    case "error":
      return { type: "error", msg: String(raw["msg"] ?? "unknown backend error") };
    default:
      return assertNever(raw as never);
  }
}

/** Download the report as Markdown, structured JSON, or the full playbook ZIP. */
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
