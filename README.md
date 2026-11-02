# ◈ GENESIS — The Ultimate Zero-Cost Business Decoding & Replication Engine

**100% free · open-source (MIT) · zero API keys · runs entirely on your machine.**

Genesis is a one-stop intelligence platform for startup founders. Feed it either an
**established company** (ADP, Stripe, Razorpay, any competitor…) or a **raw business
idea**, and it returns a 13-tab dossier: structural feasibility, decompiled feature
history with a binary build/skip roadmap, jurisdictional compliance matrix, failure
post-mortems, genesis timeline (with real SEC-filing revenue history for US-listed
subjects), pricing unit-economics with a live sandbox, market friction, burn math,
zero-cost distribution loops, technical scaffolding, Tor-routed OSINT, a phased
execution playbook, and an **adversarial red-team simulator** that cross-examines the
whole playbook. Export to Markdown, schema-versioned JSON, or a downloadable playbook ZIP.

```
┌────────────────────────────┐         NDJSON stream        ┌──────────────────────────────┐
│  Next.js 14 dashboard      │  ──────────────────────────▶ │  FastAPI intelligence engine │
│  · dark-mode console       │   logs → sections → report   │  · recon (7 free sources)    │
│  · 12-tab report viewer    │  ◀────────────────────────── │  · 12 analysis agents        │
│  · one-click MD/ZIP export │                              │  · optional Ollama + Tor     │
└────────────────────────────┘                              └──────────────────────────────┘
```

---

## What the 12 agents produce

| # | Tab | What you get |
|---|-----|--------------|
| 1 | **Structural Feasibility & Core Mechanics** | Pain-point validation from public voices, demand triggers, money-flow mechanics, systemic moats with evidence, market-timing shifts, signal score |
| 2 | **Feature Breakdown & MVP Sequencing** | Chronologically decompiled feature history (GitHub releases + Wikipedia history + changelog search), Day-1 vs growth vs enterprise classification, true-USP keyphrase mining, ordered MVP build sequence |
| 3 | **Jurisdictional & Regulatory Decoder** | US federal + state-by-state payroll/tax burden matrix (CA AB5, SUI rates, WA Cares…), India central statutory stack (MCA, GST, EPF/ESI, POSH, DPDP) + sector licenses (RBI PA, MTL, HIPAA…), severity-ranked landmine register and do-now checklist |
| 4 | **Pre-Mortem & Failure Post-Mortems** | 22 curated failure post-mortems (Zenefits, Fast, MoviePass, LendUp, Hopin…) matched to your domain, dominant death patterns, live-searched shutdown field reports, pre-mortem questions |
| 5 | **Genesis & Historical Timeline** | Company mode: decoded milestones, pivots (flagged), funding events from Wikipedia history + releases. Idea mode: 6 execution gates with kill criteria — no fake dates |
| 6 | **Pricing & Unit Economics** | Tier extraction from live pricing pages, **Wayback Machine pricing archaeology** (historical snapshots), explicit formulas: ARPA → LTV → LTV:CAC → payback, packaging-psychology detection, 3-tier recommendation |
| 7 | **Market Friction & Consumer Psychology** | Reddit/HN/review-platform voice mining into complaint clusters with shares, representative unvarnished quotes with links, demand triggers (what makes people switch) |
| 8 | **Financial Reality & Burn Calculator** | Geography-adjusted loaded-salary model, monthly burn → capital required → breakeven customers, live-editable calculator, sensitivity table, zero-sugarcoating warnings (fintech compliance costs included) |
| 9 | **Unfair Distribution & Organic Acquisition** | 13 zero-cost channels as *loops* (programmatic SEO, OSS wedge, HN cadence, India WhatsApp/LinkedIn circuit…), ranked by sector fit, each with concrete actions and time-to-first-signal |
| 10 | **Technical Architecture & Code Scaffolding** | Stack decision per sector (fintech ledger rules, payroll state-engine design…), generated starter files (FastAPI, Postgres schema, Next.js page, webhook idempotency, docker-compose, GST/OT calculators) — included in the ZIP |
| 11 | **Deep/Dark Web & Vulnerability Shield** | Tor-routed (`socks5://127.0.0.1:9050`) passive OSINT via the Ahmia onion index, search-indexed paste chatter, free HIBP breach corpus. **Lawful-use only: no marketplaces, no credentials, no interaction; illegal queries are refused** |
| 12 | **The Systematic Execution Playbook** | 6 phases with sequenced steps, gateway/KYC friction (Razorpay vs Stripe reality), KYC document pack, scaling hurdles, kill criteria |
| 13 | **Adversarial Red-Team Simulator** | A virtual panel — enterprise buyer, skeptical VC, regulatory auditor — cross-examines the generated playbook using its own sections as evidence; every challenge cites its trigger and states what answer survives. Fatal gaps must be answered or cut |

Every claim carries its source; every section survives partial scraping (blocked
sources degrade the report, never kill it).

### v1.1 institutional upgrades

- **Multi-layer source triangulation** — subject identity is anchored across
  Wikipedia (canonical name + acronym expansion), official-domain consensus,
  SEC EDGAR, and news RSS. Acronym collisions ("adPEAS" vs the payroll company
  ADP) are down-weighted before analysis ever sees them, and low-corroboration
  decodes are flagged in the console.
- **Open financial filings** — US-listed subjects are matched on SEC EDGAR
  (free, keyless): CIK, recent 10-Ks, and 10 years of annual revenue from the
  XBRL API, rendered as revenue milestones in the timeline. Private/Indian
  companies have no free structured equivalent and are reported as such.
- **Feature Decompiler v2** — a strict binary roadmap: **build now / later /
  do-not-build**, each item with its reason and a revisit gate ("after 3 written
  enterprise commitments").
- **Deeper compliance matrix** — 16 US states in a payroll-engine table
  (income tax, SUI new rate, SDI/FLI, paid leave, final-pay deadline, gotcha),
  plus India's four Labour Codes, Gratuity/Bonus Acts, and OIDAR-SaaS GST with
  export LUT.
- **Unit-economics & pricing sandbox** — live-edit ARPA, CAC, churn, margin,
  and opex; LTV/LTV:CAC/payback/breakeven recompute instantly, with per-tier
  net-margin bars after gateway drag.
- **JSON export** — `POST /api/export/json` returns a schema-versioned
  (`genesis.report/v1`) document for programmatic import; the ZIP also embeds
  `GENESIS_REPORT.json`.

---

## Quickstart (fully free, fully local)

Prerequisites: **Python 3.10+** and **Node.js 18+**. That's it.

### One command

**Windows:** double-click **`start.bat`** (or run it from any terminal).
**macOS / Linux:** `./start.sh` (or `bash start.sh`).

The script detects your toolchain, installs everything on first run (backend
virtualenv + frontend packages), starts both servers, waits for boot, and opens
your browser at the dashboard.

- Web app → <http://localhost:3000>
- API docs → <http://127.0.0.1:8000/docs>
- Stop → close the two "Genesis API/Web" windows (Windows) or Ctrl+C (macOS/Linux)

### Manual setup (what the script automates)

#### 1. Backend (FastAPI)

```bash
cd backend
python -m venv .venv

# Windows (Git Bash / PowerShell)
.venv/Scripts/python -m pip install -r requirements.txt
# macOS / Linux
# .venv/bin/python -m pip install -r requirements.txt

.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000
# macOS / Linux: .venv/bin/python -m uvicorn app.main:app --reload --port 8000
```

Health check → <http://127.0.0.1:8000/api/health>
Interactive API docs → <http://127.0.0.1:8000/docs>

#### 2. Frontend (Next.js)

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open **<http://localhost:3000>**, type a company or an idea, hit **RUN GENESIS DECODE**.

#### 3. Verify without the UI (optional)

```bash
cd backend
.venv/Scripts/python scripts/smoke_test.py company "Stripe"
.venv/Scripts/python scripts/smoke_test.py "AI meeting notes for sales teams"
```

---

## Configuration (all optional — sane defaults, zero cost)

Copy `backend/.env.example` → `backend/.env` to customize:

| Variable | Default | Effect |
|----------|---------|--------|
| `GENESIS_OFFLINE` | `0` | `1` = skip all network scraping; run on built-in knowledge bases only (great for air-gapped use, CI, demos) |
| `OLLAMA_URL` | `http://127.0.0.1:11434` | Local LLM endpoint. If Ollama is running, each section gets **LLM-sharpened narrative** on top of the deterministic analysis |
| `GENESIS_LLM_MODEL` | `llama3.2` | Any free Ollama model: `ollama pull llama3.2` |
| `TOR_PROXY` | `socks5://127.0.0.1:9050` | SOCKS5 proxy for Tab 11 |
| `TOR_ENABLED` | `1` | `0` disables the Tor probe entirely |

### Optional: Tor (powers Tab 11's anonymity routing)

- **Windows**: download the [Tor Expert Bundle](https://www.torproject.org/download/tor/), then run `tor.exe --SocksPort 9050`
- **macOS**: `brew install tor && tor --SocksPort 9050`
- **Linux**: `sudo apt install tor && sudo systemctl start tor`

Without Tor, Tab 11 automatically degrades to clearnet OSINT (Ahmia's public index +
HIBP breach corpus) and says so. Genesis never requires Tor — it's an anonymity upgrade.

### Optional: local LLM (free, private, no keys)

```bash
# https://ollama.com
ollama pull llama3.2   # ~2GB, runs on CPU if needed
```

Header chip shows `LLM: llama3.2` when detected. No Ollama → deterministic engine only;
nothing breaks.

### Optional: point the frontend elsewhere

`frontend/.env.local` (see `.env.local.example`):

```
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

---

## The zero-cost scraping engine

| Source | What it feeds | Why it's free |
|--------|--------------|---------------|
| DuckDuckGo lite/html → SearXNG → Mojeek cascade | Surface-web evidence, competitor discovery | Public keyless endpoints; automatic fallback if one blocks you |
| Wikipedia API | Genesis/summary/history/founding year | Free API |
| HN Algolia API | Developer sentiment, shutdown chatter | Free API |
| Reddit public JSON | Consumer complaints, demand triggers | Free (rate-limited; degrades softly) |
| GitHub API | Release changelogs → feature decompilation | Free unauthenticated tier |
| Wayback Machine CDX | **Historical pricing-page snapshots** | Free archive |
| Review platforms (Trustpilot/G2/Capterra) | Review intel via search-snippet aggregation only (no ToS-violating scraping) | Public search results |
| Have I Been Pwned breach corpus | Breach shield (Tab 11) | Free corpus endpoint |
| Ahmia | Lawful onion-index search (Tab 11) | Free index |
| SEC EDGAR (company_tickers, submissions, XBRL) | Real revenue history + 10-K filings (Tab 5) | Free, keyless US-government API |

Politeness rules: honest User-Agent, bounded retries, concurrency limit, rate-limit
backoff, and a session-level engine-health cache (a blocked engine is skipped, not
hammered).

## Architecture notes

- **Streaming protocol**: `POST /api/analyze/stream` emits NDJSON — `log` events feed
  the console, `section` events populate tabs live, `done` carries the full report.
- **Exports**: `POST /api/export/markdown`, `POST /api/export/json`
  (schema `genesis.report/v1` for programmatic import), and `POST /api/export/zip`
  (report + generated scaffold + embedded JSON).
- **Fail-soft everywhere**: any scraper/agent failure yields a logged warning and a
  degraded section; the pipeline always completes 12 sections.
- **Deterministic core + optional LLM**: analysis is computed from evidence + curated
  knowledge bases (compliance statutes, failure DB, channel DB). Ollama only adds
  narrative sharpening, so results never depend on a model being present.
- **Type-safe wire contract**: the frontend models the stream as a discriminated union
  (`ConsoleEvent`) and each tab's payload via `SectionDataMap` — compiled under
  `strict` + `noUncheckedIndexedAccess`, no `any` at the API boundary.

## Project structure

```
backend/
  app/
    main.py               FastAPI app (stream, health, exports)
    pipeline.py           recon → 12 agents orchestration
    models.py             request/report/evidence models
    text.py               heuristics: keyphrases, money/tier extraction, feature classification
    llm.py                optional Ollama bridge (fails soft)
    export.py             Markdown renderer + playbook ZIP builder
    scrapers/             search cascade, wikipedia, hn, reddit, github, wayback, reviews, tor
    agents/               recon + 12 analysis agents
    data/                 compliance KB (US/India), failure DB, channel DB, scaffold templates
  scripts/smoke_test.py   offline pipeline verification
frontend/
  app/                    layout, page (state machine), globals.css
  components/             InputPanel, AgentConsole, ReportViewer, ui atoms
  components/tabs/        the 12 typed tab renderers
  lib/                    types.ts (wire contract), api.ts (NDJSON client)
```

## Legal & ethical scope

Genesis performs **passive, read-only collection of publicly available information**
and cites every source. The dark-web module is lawful-use OSINT only: it reads the
Ahmia index and search-indexed paste boards, refuses illegal queries outright, never
interacts with hidden services, and includes a defensive guidance layer. Nothing here
is legal, financial, or tax advice — the compliance sections are planning-grade
intelligence synthesized from public statutes and regulator guidance.

## Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| Header shows `API offline` | Backend not running on port 8000 — start uvicorn (step 1) |
| `surface web: 0 results` | Your IP is rate-limited by search engines; Genesis auto-falls back (Wikipedia/HN/GitHub still work). Report degrades, never fails |
| Reddit: `0 posts` | Reddit rate-limits unauthenticated JSON; friction analysis leans on HN + review snippets |
| Tab 11 says `clearnet-degraded` | Tor isn't running; start `tor --SocksPort 9050` or ignore (module still delivers clearnet OSINT) |
| Ports busy | Change backend: `--port 8001` + `NEXT_PUBLIC_API_URL=http://127.0.0.1:8001` |

## License

MIT — see [LICENSE](LICENSE). Free forever, no paid tiers, no telemetry.
