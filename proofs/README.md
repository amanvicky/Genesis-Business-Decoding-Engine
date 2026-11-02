# Verification Proofs — Genesis v1.1.0

Every proof below was generated on this machine on 2026-11-02 and is **reproducible
with the commands shown in each file**. Nothing here is hand-written — these are raw
captured outputs from the running system.

## Proof index

| File | What it proves | Reproduce |
|------|----------------|-----------|
| `01_offline_pipeline_smoke.txt` | The full 13-section intelligence pipeline runs with **zero network access** (built-in knowledge bases only): `13/13 sections` | `cd backend && GENESIS_OFFLINE=1 .venv/Scripts/python scripts/smoke_test.py` |
| `02_live_adp_decode.txt` | A **live decode of a real company (ADP)** over free public sources only: multi-layer triangulation (`expansion='automatic data processing'`, 8/32 results corroborated), **SEC EDGAR revenue decode (CIK 8670, $21,947,400,000 latest annual revenue, 10-yr history)**, Google/Bing News RSS coverage, and the adversarial red-team verdict (3 fatal / 10 serious challenges) | `cd backend && GENESIS_OFFLINE=0 .venv/Scripts/python scripts/smoke_test.py company "ADP"` |
| `03_frontend_production_build.txt` | The Next.js 14 frontend compiles under **TypeScript `strict` + `noUncheckedIndexedAccess`** with zero errors | `cd frontend && npm run build` |
| `04_api_health.json` | The FastAPI backend reports liveness + capability probes (version, offline mode, Tor, local-LLM) | `curl http://127.0.0.1:8000/api/health` |
| `05_json_export_roundtrip.txt` | The structured export produces a valid **schema-versioned (`genesis.report/v1`)** JSON document: 13 sections, adversary verdict, binary roadmap, and the sandbox opex auto-fed from the burn calculator | see `backend/app/export.py`; endpoint `POST /api/export/json` |
| `screenshots/01_dashboard_adp_live_decode.png` | The actual dashboard mid-decode of ADP: live agent console streaming, tab bar, 12/13 sections decoded, 14 sources cited | run the app (`start.bat`), decode any company |
| `screenshots/02_health_chips.png` | Header capability chips (API / local LLM / Tor) degrading gracefully when the optional layers are off | automatic |

## Why offline mode matters

`01_offline_pipeline_smoke.txt` is the strongest architectural claim of the project:
Genesis produces a complete 13-section venture dossier **without a single network
call or paid API** — every module runs on built-in knowledge bases (compliance
statutes for the US + India, 22 failure post-mortems, 13 distribution channels,
scaffold generators). The live run in `02_` then shows the same pipeline enriched by
free public sources (Wikipedia, EDGAR, news RSS, HN, review snippets, Wayback).

## Repo hygiene

- `.env` files are gitignored; only `.env.example` templates are committed.
- `.venv/`, `node_modules/`, `.next/`, `__pycache__/` are gitignored.
- The screenshots contain no credentials — they show the local-only dashboard.
