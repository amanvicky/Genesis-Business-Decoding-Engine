# Changelog

All notable changes to Genesis. Format based on Keep a Changelog.

## [1.1.0] — 2026-11-03

### Added
- **Adversarial Red-Team Simulator** (Tab 13): enterprise-buyer / skeptical-VC /
  regulatory-auditor personas cross-examine the generated playbook using its own
  sections as evidence; every challenge cites its trigger and the answer that survives.
- **Multi-layer source triangulation**: subject identity anchored across Wikipedia
  (canonical name + acronym expansion), official-domain consensus, SEC EDGAR, and
  news RSS — kills acronym collisions (adPEAS vs ADP) before analysis sees them.
- **Open financial filings**: SEC EDGAR resolution (CIK, ticker, recent 10-Ks) and
  up to 10 years of annual revenue from the free XBRL API, rendered as timeline milestones.
- **Feature Decompiler v2**: strict binary roadmap — build-now / later / do-not-build,
  each item with a reason and a revisit gate.
- **Deeper compliance matrix**: 16 US states in a payroll-engine table (income tax,
  SUI, SDI/FLI, paid leave, final pay, gotchas); India Labour Codes, Gratuity/Bonus
  Acts, OIDAR-SaaS GST + export LUT.
- **Interactive pricing sandbox**: live ARPA/CAC/churn/margin/opex editing with
  instant LTV, LTV:CAC, payback, breakeven, and per-tier net-margin bars.
- **JSON export**: schema-versioned (`genesis.report/v1`) structured download; the
  ZIP embeds it too.
- Google News + Bing News RSS backends in the search cascade.

### Fixed
- Wikipedia subject resolution: disambiguation pages and pages that merely mention
  the subject (founders, partners) no longer poison decodes.
- GitHub repo matching: word-boundary + description relevance (rejects unrelated
  high-star repos sharing an acronym).
- Founding-year heuristic: sentence-scoped ("founded Stripe in Palo Alto, in 2010",
  "In 1949, Taub started…").
- Export filenames sanitized against header injection; export bodies validated.

## [1.1.1] — 2026-11-03

### Added
- **Service manager (`genesis.py`)**: one command installs, launches detached
  background services, supervises with a self-healing watchdog (whole-generation
  kill incl. orphaned children holding ports, bounded 10 restarts/hour), safe
  client-only Tor launch, `status` / `logs` / `stop` / `restart` / `doctor`.
- GitHub Actions CI: offline 13/13-section pipeline test + strict frontend build
  on every push.
- Verification proofs (`proofs/`): offline pipeline run, live ADP decode with
  EDGAR revenue match, strict build, JSON round-trip, verbatim setup session,
  and 8 real dashboard screenshots.

### Fixed
- Watchdog orphan reconciliation and port-ownership semantics (process parent chain);
  restart budget resets on fresh `up` and trips loudly instead of silently.

## [1.0.0] — 2026-11-02

- Initial release: 12-tab intelligence pipeline (FastAPI) + Next.js 14 dark-mode
  dashboard with live agent console, Markdown/ZIP export, 100% keyless operation.
