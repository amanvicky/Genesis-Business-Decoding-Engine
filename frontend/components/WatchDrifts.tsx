"use client";

import type { WatchStatus } from "@/lib/types";

/** The drift panel behind the watch chip: what changed, from what to what,
 * and which tab it came from. Read-only history — the stored memos already
 * carry the new values, this panel is the "what moved" view. */
export default function WatchDrifts({
  status,
  onAck,
}: {
  status: WatchStatus;
  onAck: () => void;
}) {
  const drifts = status.drifts;
  const unseen = drifts.filter((d) => !d.seen).length;

  if (status.running) {
    return (
      <p className="text-xs text-zinc-500">
        watch is re-decoding{status.current ? `: ${status.current}` : "…"} ({status.done}/{status.total}) — drifts land here as checks finish
      </p>
    );
  }
  if (!drifts.length) {
    return (
      <p className="text-xs text-zinc-500">
        {status.watched_count > 0
          ? `${status.watched_count} watched brief(s), nothing has drifted yet. Checks run when the dashboard opens after each interval.`
          : "Nothing watched yet — decode a company, then use “watch this subject” under the console."}
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-xs text-zinc-500">
          {drifts.length} drift alert(s){unseen > 0 ? ` · ${unseen} unread` : " · all read"}
        </span>
        {unseen > 0 && (
          <button
            onClick={onAck}
            className="border border-edge px-2 py-1 text-[11px] text-zinc-400 transition-colors duration-150 hover:border-zinc-600 hover:text-zinc-200"
          >
            mark seen
          </button>
        )}
      </div>
      <ul className="flex flex-col gap-2">
        {drifts.slice(0, 12).map((d) => (
          <li key={d.id} className={`border px-3 py-2 ${d.seen ? "border-edge/60" : "border-amber-800/60 bg-amber-950/10"}`}>
            <div className="flex items-baseline justify-between gap-3">
              <span className="text-xs font-medium text-zinc-300">{d.subject}</span>
              <span className="font-mono text-[10px] text-zinc-600">{String(d.at).slice(0, 16).replace("T", " ")}</span>
            </div>
            <ul className="mt-1.5 flex flex-col gap-1">
              {d.rows.map((r, i) => (
                <li key={i} className="text-[11px] leading-relaxed text-zinc-400">
                  <span className="text-zinc-300">{r.label}</span> {r.action}
                  {r.old ? <> · was <span className="font-mono text-zinc-300">{r.old.slice(0, 60)}</span></> : null}
                  {r.new ? <> · now <span className="font-mono text-zinc-300">{r.new.slice(0, 60)}</span></> : null}
                  <span className="ml-1 text-zinc-600">({r.tab})</span>
                </li>
              ))}
            </ul>
          </li>
        ))}
      </ul>
    </div>
  );
}
