# Pure Research Engine (the subtraction release)

## Problem Statement
How might Genesis become a pure research engine — every tab a dossier about the
decoded subject, zero calculators, zero coaching, nothing that isn't research?

## Recommended Direction
Delete the six planning agents (Financial, MarketSize, School, TechArch,
Playbook, Distribution) from the pipeline entirely — 19 tabs become 13, and
every remaining tab is evidence about the subject: features, pricing as
observed, complaints, failure analogies, timeline, filings, records, stocks,
red-team. The decision layer inherits the cut: the verdict protocol re-weights
to research-only gates (problem signal, death patterns — founder-market-fit
quiz dies with MarketSize), and the battle matrix drops the breakeven column,
tie-breaking on compliance blockers instead. Nothing that isn't research; the
call at the end survives.

## Key Assumptions to Validate
- [ ] You confirm Distribution + Playbook die too (only "amount calculations"
      was named explicitly — these two die by the rule, not by your words)
- [ ] A post-cut decode of a known subject reads like a dossier: no formulas,
      no lessons, no generated code anywhere (decode Razorpay, eyeball all 13)
- [ ] Battle + verdict still produce sane calls on the same subject as before
      the cut (same battle, re-run: does the winner still match judgment?)

## MVP Scope
IN: 6 agents deleted (pipeline, tabs, exports, advisor, ZIP scaffold), verdict
re-gated (research-only gates), battle matrix -1 column + retie, drift fields
12→10, frontend renumbered to 13 tabs, README/tests updated, v1.14 release.
OUT: hiding-instead-of-deleting, deeper research lanes (later), a planning
sibling product, re-shooting every screenshot (stale shots noted in README).

## Not Doing (and Why)
- Planning-mode toggle — you said unload, not hide; hidden code still rots
- Deeper platform lanes with the freed time — separate release, don't mix cuts
- Genesis Plan fork for the planning features — zero users, pure complexity
- Keeping the FMF quiz — it was MarketSize's data; a quiz is not research

## Open Questions
- Evidence vs compliance as the third verdict consideration (resolved: two
  research gates only — a third gate with invented thresholds would fail or
  caution every decode)
- Renumber tabs 1-13, or keep legacy numbers with gaps? (resolved: renumber)
- Does the ZIP export keep anything beyond the report once scaffolds die?
  (resolved: report only)
