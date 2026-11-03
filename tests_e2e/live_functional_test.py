#!/usr/bin/env python3
"""Live functional test against the RUNNING Genesis stack (real network).

Covers the full user journey at the HTTP level:
  health → live streaming decode (NDJSON) → exports (md/json/zip) → 422 errors
Run with the services up:   python genesis.py up --no-browser
Then:                       python tests_e2e/live_functional_test.py
"""
from __future__ import annotations

import io
import json
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = "http://127.0.0.1:8000"
WEB = "http://127.0.0.1:3000"
RESULTS: list[tuple[str, str]] = []


def check(name: str, cond: bool, detail: str = "") -> bool:
    mark = "PASS" if cond else "FAIL"
    print(f"  [{mark}] {name}" + (f" — {detail}" if detail and not cond else ""), flush=True)
    RESULTS.append((name, "PASS" if cond else "FAIL"))
    return cond


def http(method: str, url: str, body: bytes | None = None, timeout: float = 30) -> tuple[int, dict[str, str], bytes]:
    req = urllib.request.Request(url, data=body, method=method)
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, {k.lower(): v for k, v in r.headers.items()}, r.read()
    except urllib.error.HTTPError as e:
        return e.code, {k.lower(): v for k, v in e.headers.items()}, e.read()


def main() -> None:
    print("\n=== 1. health ===")
    code, _, body = http("GET", f"{API}/api/health")
    health = json.loads(body)
    check("health 200", code == 200)
    check("status ok + version", health.get("status") == "ok" and bool(health.get("version")), str(health)[:200])
    check("online mode (live stack)", health.get("offline_mode") is False, str(health.get("offline_mode")))

    print("\n=== 2. live streaming decode — Razorpay (real network) ===")
    req = {"mode": "company", "query": "Razorpay", "geography": "india", "team_size": 5, "runway_target_months": 18}
    t0 = time.time()
    code, headers, raw = http("POST", f"{API}/api/analyze/stream",
                              json.dumps(req).encode(), timeout=600)
    elapsed = time.time() - t0
    check("stream 200", code == 200, f"code={code}")
    check("NDJSON content type", headers.get("content-type", "").startswith("application/x-ndjson"),
          headers.get("content-type", ""))
    events = [json.loads(ln) for ln in raw.decode("utf-8", errors="replace").splitlines() if ln.strip()]
    types = [e.get("type") for e in events]
    sections = [e["section"] for e in events if e.get("type") == "section"]
    print(f"  ({len(events)} events in {elapsed:.0f}s — {len(sections)} sections)")
    check("no error events", "error" not in types, str([e for e in events if e.get('type') == 'error'])[:300])
    check("15/15 sections decoded", len(sections) == 15, f"got {len(sections)}: {[s['id'] for s in sections]}")
    check("adversary section ran last", bool(sections) and sections[-1]["id"] == "adversary")
    done = [e for e in events if e.get("type") == "done"]
    check("done event carries report", bool(done) and isinstance(done[0].get("report"), dict))
    report = done[0]["report"] if done else {}
    check("report subject correct", report.get("subject") == "Razorpay", str(report.get("subject")))
    check("evidence gathered (sources cited)", len(report.get("sources", [])) > 5,
          f"{len(report.get('sources', []))} sources")
    structural = report.get("sections", {}).get("structural", {})
    check("structural has verdict", bool(structural.get("summary")), structural.get("summary", "")[:120])
    check("no failed sections", all("error" not in (s.get("data") or {}) for s in sections),
          str([s['id'] for s in sections if 'error' in (s.get('data') or {})]))

    print("\n=== 3. exports (markdown / json / zip) ===")
    payload = json.dumps(report).encode()
    code, h, md = http("POST", f"{API}/api/export/markdown", payload)
    check("markdown 200", code == 200 and h.get("content-type", "").startswith("text/markdown"))
    check("markdown filename header", 'filename="GENESIS_Razorpay_' in h.get("content-disposition", ""),
          h.get("content-disposition", ""))
    check("markdown body well-formed", md.startswith("# Genesis Decoding Report — Razorpay".encode()), md[:80].decode(errors="replace"))
    code, h, js = http("POST", f"{API}/api/export/json", payload)
    parsed = json.loads(js)
    check("json 200 + schema", code == 200 and parsed.get("schema") == "genesis.report/v1")
    code, h, zp = http("POST", f"{API}/api/export/zip", payload)
    check("zip 200 + PK magic", code == 200 and zp[:2] == b"PK")
    zf = zipfile.ZipFile(io.BytesIO(zp))
    names = zf.namelist()
    check("zip has report + manifest", "GENESIS_REPORT.md" in names and "manifest.json" in names, str(names[:6]))
    check("zip report matches subject", "Razorpay" in zf.read("GENESIS_REPORT.md").decode(errors="replace")[:100])

    print("\n=== 4. live error paths ===")
    code, _, _ = http("POST", f"{API}/api/analyze/stream", json.dumps({"query": "x"}).encode())
    check("invalid query → 422", code == 422, f"code={code}")
    code, _, _ = http("POST", f"{API}/api/export/markdown", b"{broken json")
    check("broken json → 400", code == 400, f"code={code}")
    code, _, _ = http("GET", f"{API}/api/nonexistent")
    check("unknown route → 404", code == 404, f"code={code}")

    print("\n=== 5. web dashboard serves ===")
    code, h, html = http("GET", WEB)
    check("dashboard 200", code == 200, f"code={code}")
    check("dashboard is Next.js HTML", b"__next" in html.lower() or b"next" in html.lower() and b"<html" in html.lower())
    code, _, body = http("GET", f"{WEB}/nonexistent-route-xyz")
    check("unknown route → 404 (Next prod behavior)", code == 404 and b"next" in body.lower(), f"code={code}")

    print("\n" + "=" * 60)
    fails = [n for n, r in RESULTS if r == "FAIL"]
    if fails:
        print(f"FAILURES ({len(fails)}):")
        for n in fails:
            print(f"  - {n}")
        sys.exit(1)
    print(f"ALL {len(RESULTS)} LIVE CHECKS PASSED")


if __name__ == "__main__":
    main()
