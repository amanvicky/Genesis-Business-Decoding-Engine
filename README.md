# GENESIS

[![CI](https://github.com/amanvicky/Genesis-Business-Decoding-Engine/actions/workflows/ci.yml/badge.svg)](https://github.com/amanvicky/Genesis-Business-Decoding-Engine/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![Node](https://img.shields.io/badge/Node-18%2B-green.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)

Feed it a company (ADP, Stripe, Razorpay, your competitor) or just a rough idea.
It comes back with an 18-tab brief: does the model hold up, what features to copy
and what to skip, the compliance traps (per country/state), why companies like this
died, real revenue from SEC filings, pricing math you can edit live, what users
complain about, your burn and breakeven, free distribution channels, starter code,
and a red-team panel that argues with your plan. Every claim links its source.

And when you're done reading, there's a chat panel that answers questions using
your own numbers ("should I raise?", "who already does this?") and a verdict
protocol that forces a GO / NO-GO call so the brief actually ends in a decision.

No API keys. No accounts. Nothing leaves your machine.

<p align="center">
  <img src="docs/genesis-demo.gif" alt="Genesis decoding a company" width="90%">
</p>

## Run it

**Windows, like an app (recommended):** grab `Genesis-1.7.0-Setup.exe` from
[Releases](https://github.com/amanvicky/Genesis-Business-Decoding-Engine/releases)
and double-click it. Standard wizard, installs into your user folder — no admin,
no PATH changes, nothing outside its own directory. The first launch does the
heavy lifting (checks Python 3.10+ and Node 18+, privately installs anything
missing into the app folder, builds the dashboard) and then opens the dashboard
in its own window. After that: Start menu → **Genesis**. Uninstall from
Apps & Features like any other app, or just delete the folder.

**From a plain folder** (zip or `git clone`): double-click **`Genesis Setup.bat`** —
same deal, everything private to the folder. Day-to-day launcher: **`Genesis.bat`**
(no terminal after setup; the console only shows up for first-run installs).

**Already have Python 3.10+ and Node 18+:**

```bash
python genesis.py
```

First run installs the venv, npm packages and a production build, then everything
runs in the background (close the terminal, it keeps going). A watchdog restarts
crashed stuff. Then open http://localhost:3000, type a company, hit RUN.

```bash
python genesis.py status     # what's running
python genesis.py logs api   # tail logs
python genesis.py stop       # shut it down
python genesis.py doctor     # pre-flight check
python genesis.py uninstall  # stop + clean up (--deep removes venv/node_modules too)
```

Flags if you want them: `--dev`, `--no-tor`, `--no-watchdog`, `--no-browser`, `--rebuild`.

Optional extras: the installer's **Privacy layer (Tor)** checkbox downloads the
official Tor client into the app folder (client-only, Tab 11 stays clearnet-degraded
without it). **Ollama** is detected if you already run it locally — it's never
auto-installed (multi-GB, runs its own service); without it the engine is fully
deterministic and every tab still works.


## Proof it's real

Every screenshot below is a genuine capture of the running app (regenerate them
yourself with [proofs/capture.mjs](proofs/capture.mjs) — 14 shots, one command).

Landing. Type a company or an idea:

![landing](proofs/screenshots/01_landing_input_panel.png)

The agent console mid-decode — every step streams:

![console](proofs/screenshots/02_agent_console_live.png)

Structural verdict, and the compliance decoder:

![structural](proofs/screenshots/03_report_structural.png)
![compliance](proofs/screenshots/05_compliance_matrix.png)

Product DNA — the philosophy and psychology behind every feature:

![dna](proofs/screenshots/10_product_dna.png)

Market sizing and stock performance:

![sizing](proofs/screenshots/09_market_sizing.png)
![stock](proofs/screenshots/11_stock_performance.png)

Founder school — taught with your own numbers:

![school](proofs/screenshots/12_founder_school.png)

Ask Genesis (answers from your brief) and the Verdict Protocol (go / no-go):

![advisor](proofs/screenshots/13_ask_genesis_advisor.png)
![verdict](proofs/screenshots/14_verdict_protocol.png)

The full set (compliance matrix, pricing sandbox, burn calculator, red-team and
more) lives in [proofs/](proofs/).

## The 18 tabs, quickly

1. **Structural** - pain points, demand triggers, moats, a signal score
2. **Features** - feature history decompiled from GitHub releases, build-now vs do-not-build roadmap
3. **Compliance** - US federal + 16-state payroll matrix, India statutory stack (GST, EPF/ESI, DPDP...), costed checklist
4. **Pre-mortem** - 22 real failure records (Zenefits, MoviePass, Fast...) matched to your domain
5. **Timeline** - milestones and revenue history from SEC filings; idea mode gets execution gates with kill criteria instead of fake dates
6. **Pricing** - tiers, Wayback pricing history, LTV/CAC math with visible formulas, live sandbox
7. **Friction** - what users actually complain about (Reddit/HN/review mining)
8. **Burn** - geography-adjusted salaries, runway, breakeven customers, sensitivity table
9. **Distribution** - 12 zero-cost channels as repeatable loops + a first-10-customers plan
10. **Tech architecture** - stack decisions + generated starter code (ships in the ZIP)
11. **Dark web shield** - passive OSINT via Ahmia + HIBP, read-only, illegal queries refused
12. **Playbook** - 6 phases, KYC friction, scaling hurdles, kill criteria
13. **Market sizing** - bottom-up TAM/SAM/SOM with visible formulas, raise vs bootstrap math
14. **Product DNA** - the philosophy and psychology behind every feature, every term explained in plain words
15. **Founder school** - the zero-to-one knowledge transfer: what a startup is, money mechanics with your own numbers, user psychology, distribution, runway discipline, fundraising - every term defined
16. **Stock performance** - 1-year chart, 52-week range, biggest weekly rises and falls, max drawdown (private companies get the market index as context)
17. **Company deep-dive** - what the company actually does (problem in users' own words → solution → founding trigger), every feature mined from the company's own site + release trail with the issue people had before it, the reality check of what you'll come across, and the concrete marketing mechanics they use (no "they do digital marketing" filler)
18. **Red team** - an enterprise buyer, a skeptical VC and a regulator attack your plan

Every section links its sources. If a source is blocked, that one section degrades,
the rest of the run continues.

## Why it's free

Everything runs on keyless public endpoints: DuckDuckGo/SearXNG/Mojeek for search,
Wikipedia, HN Algolia, Reddit JSON, GitHub API, Wayback Machine, SEC EDGAR,
Have I Been Pwned, review snippets from search results. Honest User-Agent, bounded
retries, backoff, and a blocked engine gets skipped instead of hammered.

Optional local extras (never required): [Ollama](https://ollama.com) sharpens the
writing of each section, Tor routes Tab 11 through SOCKS5.

## How it works

- `POST /api/analyze/stream` streams NDJSON: `log` events feed the console,
  `section` events fill tabs as they finish, `done` carries the report.
- The real analysis is deterministic, built on curated knowledge bases (compliance
  statutes, failure records, channel DB). Ollama only polishes prose, so nothing
  depends on a model being present.
- Exports: markdown, schema-versioned JSON, and a ZIP with generated scaffold code.

## Project structure

```
genesis.py               service manager (install / run / supervise / stop), stdlib only
backend/app/
  main.py                FastAPI app (stream, health, advisor, verdict, exports)
  pipeline.py            recon -> 17 agents
  models.py              request/report/evidence models
  text.py                keyphrases, money/tier extraction, feature classification
  advise.py              real-time advisor (answers from your own brief)
  verdict.py             the GO / NO-GO decision protocol
  engines/               subject identity (kills acronym collisions)
  scrapers/              search cascade, wikipedia, hn, reddit, github, wayback, filings, tor
  agents/                recon + 17 analysis agents
  data/                  compliance KB (US + India), failure records, channels, scaffolds
frontend/                Next.js 14, strict TS, one typed renderer per tab
.github/workflows/       offline tests + strict build on every push
```

## Tests

I got tired of breaking things by hand, so:

```bash
cd backend && .venv/Scripts/python -m pytest tests -q     # ~275 offline tests
python scripts/smoke_test.py                              # 14/14 sections, no network
python tests_e2e/lifecycle_test.py                        # the service manager, all lifecycle stages
python tests_e2e/live_functional_test.py                  # live HTTP journey (stack must be running)
```

CI runs the pytest suite + strict frontend build on every push.

## Config

Copy `backend/.env.example` to `backend/.env`:

| Variable | Default | What it does |
|----------|---------|--------------|
| `GENESIS_OFFLINE` | `0` | `1` = no network at all, runs on the built-in KBs (CI uses this) |
| `OLLAMA_URL` | `http://127.0.0.1:11434` | local LLM endpoint, optional |
| `GENESIS_LLM_MODEL` | `llama3.2` | any model you've pulled |
| `TOR_PROXY` | `socks5://127.0.0.1:9050` | SOCKS5 for tab 11 |
| `TOR_ENABLED` | `1` | `0` disables the tor probe |

## Known issues

- `API offline` in the header: backend died, check `python genesis.py status`
- `surface web: 0 results`: search engines rate-limiting your IP, the cascade
  falls back to Wikipedia/HN/EDGAR and the report degrades but works
- Reddit gives `0 posts`: reddit rate-limits unauthenticated JSON, it is what it is
- Tab 11 says `clearnet-degraded`: no Tor installed — tick the installer's
  Privacy layer checkbox, or drop a tor.exe into `runtime\tor\` yourself
- Port already in use: `python genesis.py stop` only clears this project's
  processes, it never touches foreign apps

## License

MIT. Output is yours. Don't present the compliance notes as legal advice.
