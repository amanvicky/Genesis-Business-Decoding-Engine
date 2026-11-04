# Verification Proofs — Genesis v1.6.0

Every proof below was generated on this machine on 2026-11-04 and is **reproducible
with the commands shown in each file**. Nothing here is hand-written — these are raw
captured outputs and real screenshots from the running system.

## Screenshot tour (real captures via Playwright from the live app)

| File | What it shows |
|------|---------------|
| `screenshots/01_landing_input_panel.png` | Landing state: company/idea toggle, India–US–Global market switch, advanced parameters |
| `screenshots/02_agent_console_live.png` | A **live ADP decode mid-stream**: agent console streaming recon steps, pipeline status rail, tabs arriving |
| `screenshots/03_report_structural.png` | Finished dossier — structural verdict, pain points, moats with evidence, signal score |
| `screenshots/04_feature_binary_roadmap.png` | Feature Decompiler v2: **build-now / later / do-not-build** binary roadmap with gates |
| `screenshots/05_compliance_matrix.png` | Jurisdictional decoder: landmine register + **US payroll-engine matrix** (16 states) |
| `screenshots/06_pricing_sandbox.png` | Pricing tab with the **interactive unit-economics sandbox** (live LTV/CAC/payback recomputation, per-tier margin bars) |
| `screenshots/07_burn_calculator.png` | Financial reality: live-editable burn calculator, sensitivity table, blunt runway warnings |
| `screenshots/08_adversary_redteam.png` | **Adversarial Red-Team Simulator**: buyer/VC/auditor personas with fatal & serious challenges |
| `screenshots/09_market_sizing.png` | Market sizing: bottom-up TAM/SAM/SOM with formulas, raise vs bootstrap, founder-market-fit checklist |
| `screenshots/10_product_dna.png` | **Product DNA**: the philosophy + psychology behind every feature, with named principles and a plain-words glossary |
| `screenshots/11_stock_performance.png` | Stock performance: 1-year sparkline, 52-week range, biggest weekly rises and falls, max drawdown |
| `screenshots/12_founder_school.png` | **Founder School**: the zero-to-one curriculum, money lessons taught with the dossier's own numbers |
| `screenshots/13_ask_genesis_advisor.png` | **Ask Genesis**: real-time advisor answering "what is churn?" with a link into the right lesson |
| `screenshots/14_verdict_protocol.png` | **Verdict Protocol**: FMF answered, gates computed, GO/NO-GO decision badge + downloadable memo |

Reproduce: start the app (`python genesis.py`), open `http://localhost:3000`,
decode any company, and click through the tabs.

## Pipeline & engineering proofs

| File | What it proves | Reproduce |
|------|----------------|-----------|
| `01_offline_pipeline_smoke.txt` | The full 17-section intelligence pipeline runs with **zero network access** (built-in knowledge bases only): `13/13 sections` | `cd backend && GENESIS_OFFLINE=1 .venv/Scripts/python scripts/smoke_test.py`  (expect `17/17 sections`) |
| `02_live_adp_decode.txt` | A **live decode of a real company (ADP)** over free public sources only: multi-layer triangulation (`expansion='automatic data processing'`, corroborated results), **SEC EDGAR revenue decode (CIK 8670, $21,947,400,000 latest annual revenue, 10-yr history)**, Google/Bing News RSS coverage, and the adversarial red-team verdict | `cd backend && GENESIS_OFFLINE=0 .venv/Scripts/python scripts/smoke_test.py company "ADP"` |
| `03_frontend_production_build.txt` | The Next.js 14 frontend compiles under **TypeScript `strict` + `noUncheckedIndexedAccess`** with zero errors | `cd frontend && npm run build` |
| `04_api_health.json` | The FastAPI backend reports liveness + capability probes (version, offline mode, Tor, local-LLM) | `curl http://127.0.0.1:8000/api/health` |
| `05_json_export_roundtrip.txt` | The structured export produces a valid **schema-versioned (`genesis.report/v1`)** JSON document: 17 sections, adversary verdict, binary roadmap, market sizing, school, sandbox opex auto-fed from the burn calculator | endpoint `POST /api/export/json` |
| `06_setup_and_launch_cli.txt` | A **verbatim service-manager session**: `stop` then `up` — auto-detection, background launch, health gates, watchdog, and the operations cheatsheet | `python genesis.py stop && python genesis.py` |

## Why offline mode matters

`01_offline_pipeline_smoke.txt` is the key architectural claim:
Genesis produces a complete 17-section venture dossier **without a single network
call or paid API** — every module runs on built-in knowledge bases (compliance
statutes for the US + India, 22 failure records, 12 distribution channels,
scaffold generators). The live run in `02_` then shows the same pipeline enriched by
free public sources (Wikipedia, EDGAR, news RSS, HN, review snippets, Wayback).

## Repo hygiene

- `.env` files are gitignored; only `.env.example` templates are committed.
- `.venv/`, `node_modules/`, `.next/`, `runtime/`, `logs/` are gitignored.
- The screenshots contain no credentials — they show the local-only dashboard.


## Screenshot capture tooling

[capture.mjs](capture.mjs) drives headless Edge (puppeteer-core) through a full
decode and captures all 14 shots above in one run:

```bash
npm i puppeteer-core          # in any scratch dir with capture.mjs copied in
node capture.mjs <outDir> "Apple"
```
