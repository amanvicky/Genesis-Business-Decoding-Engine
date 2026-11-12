# Verification Proofs — Genesis v1.14.0

Every proof below was generated on this machine on 2026-11-12 and is **reproducible
with the commands shown in each file**. Nothing here is hand-written — these are raw
captured outputs and real screenshots from the running system.

## Screenshot tour (real captures via headless Edge from the live app)

| File | What it shows |
|------|---------------|
| `screenshots/01_landing_input_panel.png` | Landing state: four modes — company name, website URL, raw idea, and the idea battle |
| `screenshots/02_agent_console_live.png` | A live Notion decode mid-recon: agent console streaming, pipeline rail waiting on the thirteen agents |
| `screenshots/03_report_structural.png` | Structural verdict, pain points as voiced publicly, moats with evidence, the signal score |
| `screenshots/04_feature_binary_roadmap.png` | Feature breakdown: the **build-now / later / do-not-build** binary roadmap with gates |
| `screenshots/05_compliance_matrix.png` | Jurisdictional decoder: landmine register + the costed launch checklist |
| `screenshots/06_premortem_post_mortems.png` | Pre-mortem: matched collapsed operators, dominant death patterns, counter-moves |
| `screenshots/07_pricing_observed.png` | Pricing as observed: the tiers the company actually charges, wayback history, packaging psychology — no LTV:CAC math |
| `screenshots/08_product_dna.png` | **Product DNA**: the philosophy + psychology behind every feature, named principles, plain-words glossary |
| `screenshots/09_stock_performance.png` | Stock tab for a private subject: honest index context ("Notion is not publicly traded") — the S&P 500 year, biggest rises/falls, drawdown |
| `screenshots/10_public_record.png` | Public record: RDAP domain record, Wikidata legal facts, registry mentions marked *verify each* |
| `screenshots/11_adversary_redteam.png` | **Adversarial Red-Team Simulator**: buyer/VC/auditor personas with fatal & serious challenges |
| `screenshots/12_ask_genesis_advisor.png` | **Ask Genesis**: real-time advisor answering "what kills companies like this?" from the brief's own evidence |
| `screenshots/13_verdict_protocol.png` | **Verdict Protocol v2**: two research-only gates computed from the evidence, decision badge, memo download — no quiz |
| `screenshots/14_battle_matrix.png` | **The Idea Battle**: a raw idea vs the incumbent by URL, decoded one at a time, winner decided by the rule matrix |

Reproduce: start the app (`python genesis.py`), open `http://localhost:3000`,
decode any company, and click through the thirteen tabs.

## Pipeline & engineering proofs

| File | What it proves | Reproduce |
|------|----------------|-----------|
| `01_offline_pipeline_smoke.txt` | The full 13-agent research pipeline runs with **zero network access** (built-in knowledge bases only): `13/13 sections` | `cd backend && GENESIS_OFFLINE=1 .venv/Scripts/python scripts/smoke_test.py`  (expect `13/13 sections`) |
| `02_live_adp_decode.txt` | A **live decode of a real company (ADP)** over free public sources only: multi-layer triangulation, **SEC EDGAR revenue decode**, news RSS coverage, and the adversarial red-team verdict | `cd backend && .venv/Scripts/python scripts/smoke_test.py company "ADP"` |
| `03_frontend_production_build.txt` | The Next.js 14 frontend compiles under **TypeScript `strict` + `noUncheckedIndexedAccess`** with zero errors | `cd frontend && npm run build` |
| `04_api_health.json` | The FastAPI backend reports liveness + capability probes (version, offline mode, Tor, local-LLM) | `curl http://127.0.0.1:8000/api/health` |
| `05_json_export_roundtrip.txt` | The structured export produces a valid **schema-versioned (`genesis.report/v1`)** JSON document: 13 sections round-tripped through `POST /api/export/json` | endpoint `POST /api/export/json` |
| `06_setup_and_launch_cli.txt` | A **verbatim service-manager session**: `status` then `doctor` — health gates, watchdog supervision, ports held by this project | `python genesis.py status && python genesis.py doctor` |

## Why offline mode matters

`01_offline_pipeline_smoke.txt` is the key architectural claim:
Genesis produces a complete 13-section research brief **without a single network
call or paid API** — every module runs on built-in knowledge bases (compliance
statutes for the US + India, the failure-analog library, the DNA principle
glossaries). The live run in `02_` then shows the same pipeline enriched by
free public sources (Wikipedia, EDGAR, news RSS, HN, review snippets, Wayback).

## Repo hygiene

- `.env` files are gitignored; only `.env.example` templates are committed.
- `.venv/`, `node_modules/`, `.next/`, `runtime/`, `logs/` are gitignored.
- The screenshots contain no credentials — they show the local-only dashboard.


## Screenshot capture tooling

[capture.mjs](capture.mjs) drives headless Edge (puppeteer-core) through a full
decode and captures all 14 shots above in one run — it also refreshes the
landing page's static captures (`frontend/public/captures/`) from the same
decode before re-shooting the landing:

```bash
npm i puppeteer-core          # in any scratch dir with capture.mjs copied in
node capture.mjs <outDir> "Notion" <frontend/public/captures>
```
