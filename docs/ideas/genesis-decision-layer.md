# Genesis: The Decision Layer

## Problem Statement
How might a founder go from "I decoded my idea" to "I decided what to do about it" —
with the evidence attached, in one sitting, for free?

## Recommended Direction
Build the **Decision Layer** in two moves. First, the **Verdict Protocol**: every
decode ends in a forced decision flow — founder-market-fit checklist, kill-gate
answers, market-math verdict — that renders a one-page GO / NO-GO / REBUILD memo,
deterministic fields only (KB math, compliance counts, red-team fatals), exported
alongside the existing markdown/ZIP. Second, **Idea Battle**: run 2–3 ideas through
the pipeline and render a tab-by-tab diff with a portfolio recommendation. Both are
orchestration of data the pipeline already produces — no new research surface.

Once memos are stable, ship **Reality Watch**: `genesis.py watch` re-decodes on a
schedule, diffs against the stored memo, and alerts only on real drift (pricing
rows, compliance changes, new failure matches). Drift summaries become the payload
of a KB-contribution PR template — the flywheel starts when users exist, not before.

## Key Assumptions to Validate
- [ ] Memo stability: same idea, two decodes → same verdict fields (test: Razorpay ×2)
- [ ] Honest checklist completion: run one real idea through the protocol yourself
- [ ] Verdict trust: does the memo's call match your judgment on a known case?
- [ ] Real drift exists: 3 weekly re-decodes of one company → measure actual diffs
- [ ] Alert budget: <3 alerts/week, each with an action attached

## MVP Scope
IN: memo generator (one page, deterministic fields, markdown+HTML), decision flow
UI (6 questions, wired to existing FMF/kill-gates), Idea Battle diff view (tab ×
idea matrix), `genesis.py watch` with memo-diff alerts.
OUT: KB contribute command (template only), hosted anything, Ollama-dependent
verdicts, diffing of scraped sentences.

## Not Doing (and Why)
- **KB contribute command** — no contributors yet; the flywheel needs an audience first
- **Operating Copilot (real-books integration)** — scope creep into accounting; graveyard of founder tools
- **The Interrogator (chat-first inversion)** — bold v2 bet; it rewrites the core flow you just hardened
- **Hosted sharing** — shareability comes free with the memo file; nothing leaves disk
- **Revenue mechanics** — free/local is the identity; revisit only after real decisions are documented

## Open Questions
- What exactly is a "real drift"? (needs a threshold definition per tab)
- Does the memo belong in the ZIP export or as a separate artifact?
- Should Idea Battle reuse one browser session or spawn parallel pipelines?
