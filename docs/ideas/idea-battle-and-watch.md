# Idea Battle + Reality Watch

## Problem Statement
How might a founder compare 2–3 ideas side by side on evidence, then keep watching the chosen one — free, local, without re-reading 19 tabs by hand?

## Recommended Direction
Ship Vault → Battle → Watch as one pipeline of stored state. Every decode is persisted to `briefs/` (JSON + markdown, capped at 3 per subject). Battle mode takes 2–3 typed ideas, decodes them **sequentially** (one IP, no parallel bans), and renders a deterministic matrix — signal score, verdict call, red-team fatals, breakeven customers, compliance blockers — with a rule-based winner and one LLM-written paragraph of verdict prose; ties resolve to PENDING, never fake confidence. Watch marks vault entries as watched: when the dashboard is opened after the interval, the backend lazily re-decodes headless, diffs KB-stable fields against the stored memo, and alerts on three tiers — silent log always, markdown drift memo on real change, dashboard drift chip with a per-tab panel.

## Key Assumptions to Validate
- [ ] Memo stability: Razorpay decoded twice same-day → identical KB-stable fields (run before Watch ships)
- [ ] One real battle on your own ideas: does the rule-winner match your judgment?
- [ ] One real watch cycle: does a deliberate change (e.g., a rival's pricing move surfaces) produce exactly one drift memo?
- [ ] A friend completes battle + watch without asking you anything

## MVP Scope
IN: pure field extractor (tested), battle mode UI (typed ideas, sequential, matrix, winner, LLM prose line), `briefs/` vault (JSON+md, cap 3/subject), lazy watch on dashboard-open + `genesis.py watch` manual trigger, ~8 bounded drift signals with thresholds, drift chip + panel (no 20th tab).
OUT: idea-vs-URL battles, competitor watchlist, KB contribution, parallel decodes, LLM-judged winner (one prose call only), history-picker UI in battle.

## Not Doing (and Why)
- **Idea vs its rivals by URL** — next release; battles typed ideas first
- **Evidence-reuse speedup** — shared sweeps contaminate the comparison; battles must stay independent
- **Competitor watchlist** — real value, scope creep until one friend completes one cycle
- **Battle-from-history picker UI** — vault stores now, picker ships when there's history worth picking
- **A 20th tab** — the drift chip avoids renumbering your 19 tabs and the advisor's references

## Open Questions
- Exact winner-rule weights (signal score vs verdict call vs fatals vs breakeven)?
- Initial drift thresholds per field — start strict (<3 alerts/week) and loosen?
- Should battles offer an "LLM off, faster" toggle, or always keep the final prose call?
