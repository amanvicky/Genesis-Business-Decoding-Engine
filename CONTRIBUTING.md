# Contributing to Genesis

Thanks for considering a contribution — this project exists to prove that serious
venture intelligence can be 100% free and keyless. PRs are welcome.

## The three commandments

1. **Keyless or nothing.** No feature may require a paid API, an account, or a key.
   Free public sources only (Wikipedia, EDGAR, news RSS, HN, GitHub, Wayback, …).
2. **Fail soft, cite everything.** Any scraper or agent failure must degrade its
   own section — never kill the pipeline — and every claim must carry a source link.
3. **Zero-sugarcoating.** Analysis sections state evidence depth and uncertainty.
   No fluff, no filler timelines, no "it depends".

## Quick dev loop

```bash
python genesis.py --dev        # backend + frontend with hot reload
python genesis.py logs api     # watch the pipeline
cd backend && .venv/Scripts/python scripts/smoke_test.py   # offline 13/13 check
```

- Backend: Python 3.10+, FastAPI, stdlib-first. Agents live in `app/agents/`,
  free scrapers in `app/scrapers/`, curated knowledge bases in `app/data/`.
- Frontend: Next.js 14 App Router, TypeScript **strict** (no `any` at the wire
  boundary), Tailwind. Tab renderers in `components/tabs/` are typed through
  `lib/types.ts`'s `SectionDataMap`.
- The wire contract is NDJSON: `log` → `status` → `section` → `done`. Keep it.

## Before opening a PR

- `python scripts/smoke_test.py` from `backend/` prints 13/13 offline — CI runs
  the same check, so run it first.
- `npm run build` from `frontend/` must pass under strict TS.
- New scraper? It must (a) be free and keyless, (b) fail soft, (c) add its
  sources to the evidence list, (d) respect robots/ToS — snippet aggregation
  over scraping paywalled pages.
- New knowledge-base rows (compliance items, failure post-mortems, channels)?
  Great — these are the highest-value PRs. Keep the `(item, why, cost, time,
  severity)` shape and cite the statute or source in the text.

## Reporting issues

Include: the subject you decoded, the console log (`python genesis.py logs api`),
and what you expected vs got. Security issues: see below — do not open a public
issue; use GitHub's private security advisory.

## Scope guard

PRs that add paid services, scraping-evasion, or interactive dark-web access will
be declined — that's a design principle, not an oversight.
