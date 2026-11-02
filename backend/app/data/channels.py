"""Zero-cost distribution channel database (Tab 9 backbone).

Every entry is a LOOP (repeatable, compounding), not a one-off tactic.
`fit` lists sectors where the loop compounds hardest; `geo` gates regionally.
"""
from __future__ import annotations

Channel = dict

CHANNELS: list[Channel] = [
    {
        "name": "Programmatic SEO on long-tail jobs-to-be-done",
        "loop": "Every solved user problem becomes an indexable page → rankings compound → users arrive with intent → their data/queries generate new pages.",
        "effort": "high (engineering-led)",
        "time_to_first_signal": "2–4 months",
        "actions": [
            "Map the 50–500 recurring jobs users do (e.g., 'convert paystub to W2', 'CA payroll tax calculator').",
            "Build one template engine + database, publish a page per job with a genuinely functional tool or answer.",
            "Interlink ruthlessly; submit sitemap; measure rank movement weekly with a free rank checker.",
        ],
        "fit": ["saas", "devtools", "fintech", "commerce", "edu"],
        "geo": ["us", "global", "india"],
    },
    {
        "name": "Hacker News launch + Show HN cadence",
        "loop": "Launch → front-page traffic → emails/signup spike → you ship the top comment request within 72h → post again with the shipped feature. Repeatable every 4–8 weeks.",
        "effort": "low (but timing-sensitive)",
        "time_to_first_signal": "days",
        "actions": [
            "Post as Show HN Tuesday–Thursday, 7–9am ET; title = what it does, no adjectives.",
            "Answer every comment in the first 3 hours; never be defensive.",
            "Keep a public changelog link ready — HN rewards visible shipping velocity.",
        ],
        "fit": ["devtools", "saas", "fintech"],
        "geo": ["us", "global"],
    },
    {
        "name": "Open-source wedge (GitHub as distribution)",
        "loop": "Free OSS library/tool solves 20% of the problem → stars → contributors → issues become a sales pipeline for the paid 80%.",
        "effort": "high",
        "time_to_first_signal": "1–3 months",
        "actions": [
            "Extract one genuinely useful internal module (a validator, a tax-rate table, a parser) and open-source it.",
            "Write a README that solves the problem completely before mentioning your product.",
            "Add a non-invasive 'powered by' + GitHub Sponsors; seed discussions by answering adjacent Stack Overflow questions.",
        ],
        "fit": ["devtools", "saas", "fintech"],
        "geo": ["us", "global", "india"],
    },
    {
        "name": "Reddit value-first participation",
        "loop": "Answer domain questions thoroughly in niche subs (r/smallbusiness, r/payroll, r/IndiaInvestments) → profile/link in bio converts → posts get saved and keep converting for years.",
        "effort": "medium",
        "time_to_first_signal": "2–6 weeks",
        "actions": [
            "Search your exact problem phrases across Reddit; answer the top 30 threads with real substance, no links in body.",
            "Build one flagship long-form post per month on the sub's recurring pain (rules-dense, cited).",
            "Track which threads convert via UTM'd bio link.",
        ],
        "fit": ["saas", "fintech", "payroll", "commerce", "health"],
        "geo": ["us", "global", "india"],
    },
    {
        "name": "Product Hunt + free-tool lead magnet",
        "loop": "Ship a small free tool (calculator, checker, generator) → PH launch → tool ranks for its own query → emails collected → convert to main product.",
        "effort": "medium",
        "time_to_first_signal": "2–6 weeks",
        "actions": [
            "Build the smallest calculator that answers a compliance/pricing question people google (e.g., 'take-home salary calculator IN').",
            "Launch on PH with a founder story, not a feature list.",
            "Email-tool signups within 72h of launch while PH ranking lasts.",
        ],
        "fit": ["saas", "fintech", "payroll", "edu"],
        "geo": ["us", "global", "india"],
    },
    {
        "name": "Integration/marketplace listings (Stripe, Shopify, Slack, Zoho)",
        "loop": "App-store listing rides the host platform's search traffic → installs are intent-rich → each install is a warm lead with zero CAC.",
        "effort": "medium",
        "time_to_first_signal": "1–3 months",
        "actions": [
            "Ship one integration for the platform where your users already are; meet 100% of its app-review guidelines first try.",
            "Optimize listing keywords like ASO; screenshot the workflow, not the UI.",
            "Ask every integration user for a marketplace review within week one.",
        ],
        "fit": ["saas", "fintech", "commerce", "payroll"],
        "geo": ["us", "global", "india"],
    },
    {
        "name": "Comparison/alternative pages (the 'X alternative' ladder)",
        "loop": "Rank for 'CompetitorX alternative/pricing/review' → intercept switchers at the exact decision moment → convert churn from incumbents.",
        "effort": "medium",
        "time_to_first_signal": "1–3 months",
        "actions": [
            "Publish honest, specific comparison pages vs. the 5 nearest competitors (feature tables, real pricing math).",
            "Include a migration path (importers, docs) — switchers convert on de-risking.",
            "Refresh quarterly; comparison pages rot and Google notices.",
        ],
        "fit": ["saas", "fintech", "payroll", "devtools"],
        "geo": ["us", "global", "india"],
    },
    {
        "name": "India: WhatsApp + LinkedIn founder-led selling",
        "loop": "LinkedIn build-in-public posts in the Indian SaaS/bFounder circuit → DMs → WhatsApp demos → community referrals between founders.",
        "effort": "low-medium",
        "time_to_first_signal": "1–4 weeks",
        "actions": [
            "Post 3×/week: one metric, one mistake, one customer conversation (numbers, not adjectives).",
            "Join SaaSBoomi, Bangalore Insider, India SaaS communities; answer compliance questions where founders panic-search.",
            "Convert every paying user into a WhatsApp referral ask at the moment of first value.",
        ],
        "fit": ["saas", "fintech", "payroll", "edu", "logistics"],
        "geo": ["india"],
    },
    {
        "name": "Community sponsorships at zero cost (Discord/Slack mods)",
        "loop": "Offer free accounts + genuine help in the communities where your ICP congregates → become the known answer → moderators refer you.",
        "effort": "medium",
        "time_to_first_signal": "2–8 weeks",
        "actions": [
            "Identify 10 communities (industry Slacks, Discords); read rules; help without links for 2 weeks before mentioning anything.",
            "Negotiate a free 'community plan' in exchange for a channel/partner badge.",
        ],
        "fit": ["devtools", "saas", "commerce"],
        "geo": ["us", "global", "india"],
    },
    {
        "name": "Teardown/case-study content engine",
        "loop": "Publish reverse-engineered teardowns (pricing, growth, failures — exactly what Genesis produces) → ranks + gets shared by the companies' own employees → inbound authority.",
        "effort": "medium-high",
        "time_to_first_signal": "1–3 months",
        "actions": [
            "One 2,000-word teardown per week using only public data; cite everything.",
            "Email the teardown to practitioners quoted/mentioned; ask for corrections (they share it).",
        ],
        "fit": ["saas", "fintech", "commerce", "devtools"],
        "geo": ["us", "global", "india"],
    },
    {
        "name": "Cold email that doesn't need volume",
        "loop": "20 hyper-personalized emails/week to companies already feeling the pain (job posts reveal it) → 10–20% reply rates at true zero media cost.",
        "effort": "medium",
        "time_to_first_signal": "1–2 weeks",
        "actions": [
            "Mine job boards: companies hiring a 'payroll manager' have a payroll problem — sell before they hire.",
            "Reference the specific artifact (their job post, their pricing page bug) in line 1.",
            "Plain text, one ask, no calendar link in email #1.",
        ],
        "fit": ["saas", "payroll", "fintech", "logistics", "devtools"],
        "geo": ["us", "global", "india"],
    },
    {
        "name": "YourStory / Inc42 / regional press (India)",
        "loop": "Fundraise-free founder stories with a data hook get picked up by tier-2 press → backlinks + credibility + inbound for months.",
        "effort": "low",
        "time_to_first_signal": "2–6 weeks",
        "actions": [
            "Pitch a data story ('we analyzed 200 GST notices...'), not a funding story.",
            "Offer the underlying dataset to the journalist — exclusive data is the only free currency press values.",
        ],
        "fit": ["saas", "fintech", "edu", "commerce", "health"],
        "geo": ["india"],
    },
]


def channels_for(sector: str, geography: str, limit: int = 7) -> list[Channel]:
    geo = geography if geography != "global_" else "global"
    scored = []
    for ch in CHANNELS:
        fit = 2 if sector in ch["fit"] else (1 if sector == "generic" else 0)
        geo_ok = geo in ch["geo"] or "global" in ch["geo"]
        if fit and geo_ok:
            scored.append((fit, ch))
    scored.sort(key=lambda x: -x[0])
    return [ch for _, ch in scored[:limit]]
