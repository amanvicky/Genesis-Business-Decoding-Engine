"""Company Deep-Dive KB (Tab 11 backbone).

Three content layers:
  MARKETING_MECHANICS - concrete growth mechanics (how companies actually
  market), each with detection keywords, the hook it promotes, and the
  psychological basis. No "they do digital marketing" filler.
  REALITY_CHECKS - the things a builder will actually come across, framed as
  observations of what happens, not instructions.
  USER_ISSUES - how people experienced the problem BEFORE each product pattern
  existed (feeds the feature inventory's "the issue they had" layer).
"""
from __future__ import annotations

Mechanic = dict

# detection keywords (lowercase) -> the concrete marketing mechanic
MARKETING_MECHANICS: list[Mechanic] = [
    {
        "name": "The product is the ad (freemium funnel)",
        "kw": ["free tier", "freemium", "free plan", "free forever", "free trial"],
        "how": "The free version spreads by being used: every free user shows the product to teammates, and the upgrade moment is engineered to arrive when the user already depends on it. The company spends on servers instead of ads.",
        "promotes": "the free tier itself - it's the hook everything else hangs on",
        "psych": "Foot-in-the-door + ownership: saying yes to free is effortless, and once their work lives inside it, leaving feels like losing property.",
    },
    {
        "name": "Search real estate (SEO engine)",
        "kw": ["blog", "guide", "documentation", "template gallery", "seo", "rank"],
        "how": "Every answer a customer might search for becomes a page the company owns. The pages compound: a library of 500 genuinely useful pages keeps pulling free intent traffic for years after publishing.",
        "promotes": "solutions to long-tail problems ('how to do X'), with the product positioned as the shortcut",
        "psych": "Reciprocity + authority: teach first, and the reader trusts the tool that taught them.",
    },
    {
        "name": "Community gravity",
        "kw": ["community", "forum", "discord", "subreddit", "user group", "ambassador"],
        "how": "A place where users help each other, so every problem solved publicly becomes onboarding for the next thousand. The community answers questions the company never has to, and membership becomes part of the product's identity.",
        "promotes": "belonging and status inside the user group",
        "psych": "Social proof at scale + identity: 'people like me use this' is the strongest adoption signal there is.",
    },
    {
        "name": "Users-as-salesforce (referral loops)",
        "kw": ["referral", "invite", "give get", "refer a friend", "affiliate"],
        "how": "Structured incentives turn the user base into the acquisition channel: both sides get something, the invitation arrives from a trusted person instead of an ad, and the loop compounds while it stays honest.",
        "promotes": "the invite moment inside the product, timed to when the user just got value",
        "psych": "Reciprocity + social currency: gifts create the pull; inviting friends makes the inviter look sharp.",
    },
    {
        "name": "Press & launch moments",
        "kw": ["launch", "announc", "funding", "raised", "unveil", "introduc"],
        "how": "Every milestone (funding, major release, acquisition) is manufactured into a news moment. Each spike of attention is captured with a clear next step for the newcomers, then the press momentum is banked as credibility for months.",
        "promotes": "the milestone itself as proof the company is real and moving",
        "psych": "Authority + social proof: 'featured in X' and 'just raised' transfer credibility from institutions.",
    },
    {
        "name": "App-store & platform presence",
        "kw": ["app store", "play store", "ios app", "android app", "chrome extension", "plugin"],
        "how": "Living inside the stores and platforms where intent already exists: the store's search, ratings and 'similar apps' lists do the distribution. Each platform review is permanent social proof.",
        "promotes": "the mobile/extension surface of the same product, catching users in a different context",
        "psych": "Availability + default bias: being present in the moment of need beats being better later.",
    },
    {
        "name": "Creator & influencer leverage",
        "kw": ["influencer", "creator", "youtube", "reviewer", "sponsor", "podcast"],
        "how": "Borrowing audiences that took someone else a decade to build: creators demonstrate the product to an audience that already trusts them, and the demo is content, not an interruption.",
        "promotes": "a visible workflow, so viewers see the product solving a real problem in real time",
        "psych": "Parasocial trust: the audience treats the creator's recommendation as advice from a friend.",
    },
    {
        "name": "Sales-led enterprise motion",
        "kw": ["contact sales", "book a demo", "enterprise plan", "account executive", "request demo"],
        "how": "High-value customers are pursued personally: demos, pilots, procurement support. Slower and costlier per customer, but each win is a large multi-year contract that funds the rest.",
        "promotes": "the enterprise controls and compliance posture, because procurement is the real buyer",
        "psych": "Authority + risk aversion: the buyer's fear of blame is soothed by human hand-holding.",
    },
    {
        "name": "Paid acquisition",
        "kw": ["ad spend", "ads", "campaign", "sponsored", "ppc", "retarget"],
        "how": "Renting attention at a known price: ads convert only if the CAC math works, so this mechanic appears when the unit economics are proven and every rupee of spend has a measured payback.",
        "promotes": "the single highest-intent feature, tested across dozens of variants",
        "psych": "Intent capture: reaching people at the exact moment they searched for the problem.",
    },
    {
        "name": "Partnerships & bundles",
        "kw": ["partner", "bundle", "integrated with", "reseller", "white label"],
        "how": "Riding another company's distribution: bundling puts the product in front of an established user base as a default or add-on, converting without a separate marketing motion.",
        "promotes": "the integration story: 'already works with what you have'",
        "psych": "Default bias + borrowed trust from the partner's brand.",
    },
    {
        "name": "Events, webinars & sponsorships",
        "kw": ["conference", "webinar", "sponsor", "event", "meetup", "summit"],
        "how": "Being physically/virtually present where the industry gathers: a talk or booth converts attention into relationship, and the recorded talk keeps marketing for years.",
        "promotes": "the company's expertise, with the product demonstrated in context",
        "psych": "Authority + in-group belonging: showing up where the tribe meets signals membership.",
    },
    {
        "name": "Comparative & category content",
        "kw": ["vs", "alternative to", "comparison", "best ", "review"],
        "how": "Owning the comparison moment: when a buyer searches 'X vs Y' or 'X alternative', the company's own comparison page is the first thing they read - the highest-intent traffic there is.",
        "promotes": "honest-looking comparisons where the company's strengths are the deciding columns",
        "psych": "Choice architecture: whoever frames the comparison decides the winner.",
    },
]

# the reality checks: things a builder WILL come across. observations, not advice.
REALITY_CHECKS: list[dict] = [
    {"area": "Support is the hidden second product",
     "what": "Every feature that ships generates questions forever. The inbox grows with the user count, and early on the founders ARE the support team - which is where the real product feedback comes from."},
    {"area": "Compliance arrives before you feel ready",
     "what": "The moment real users hand over real data, registrations, filings and privacy rules apply - regardless of company size. The cost is front-loaded: some obligations are due before the first invoice."},
    {"area": "The first version will embarrass you",
     "what": "Early users see the rough edges, outages happen at the worst times, and the roadmap you were sure about gets rewritten by what the first paying customers actually want."},
    {"area": "Churn is silent and constant",
     "what": "Users leave without saying goodbye. Some months the leak is bigger than the inflow even while new signups look healthy - the scoreboard that matters is cohort retention, not total signups."},
    {"area": "Cash cycles lag effort",
     "what": "Invoices are paid late, trials expire unpaid, and the gap between work done and money received is measured in months. Plans that assume instant cashflow break on this alone."},
    {"area": "Competition responds",
     "what": "The moment something works, incumbents bundle it, clones launch it cheaper, and the differentiation that worked last quarter needs a new answer."},
    {"area": "Data protection is a daily obligation",
     "what": "Every user record is a liability with a shelf life: access control, deletion requests, breach response. The rules apply from the first real user, not from some later 'scale' milestone."},
    {"area": "Growth is not a straight line",
     "what": "Weeks of flat, then a spike, then flat again. The flat weeks are where most founders quit - the curve only looks inevitable in retrospect."},
]

# how people experienced the problem BEFORE each product pattern existed
USER_ISSUES: dict[str, str] = {
    "Freemium / free tier": "Before: you sat through a sales call and signed a contract just to touch the product. Trying anything meant procurement.",
    "Streaks & habit mechanics": "Before: motivation died silently. Nothing tracked your consistency, so skipping once quietly became skipping forever.",
    "Onboarding checklists & progress bars": "Before: an empty dashboard and a PDF manual. Most users never found the value and quit without ever telling anyone why.",
    "Notifications & digests": "Before: you had to remember to come back. Out of sight, out of mind - and the account quietly died.",
    "Referrals & invites": "Before: you recommended the tool in conversation and got nothing, and the company paid an ad network for the same customer.",
    "Templates & starter content": "Before: the blank page. Hours of setup before any value, and most people gave up mid-setup.",
    "Integrations & ecosystem": "Before: copy-paste between tools, export/import rituals, and re-entering the same data in five places.",
    "Enterprise controls (SSO, audit, roles)": "Before: shared passwords, no audit trail, and IT blocking the tool because nobody could prove who did what.",
    "Urgency & scarcity mechanics": "Before: 'I'll decide later' - and later never came, because nothing marked the decision as expiring.",
    "Social proof surfaces": "Before: trusting the vendor's own claims, with no way to see what people like you experienced.",
    "Personalization & recommendations": "Before: one-size-fits-all. You dug through irrelevant content to reach the part that mattered to you.",
    "AI copilots & auto-magic": "Before: the boring 80% of the task was manual - formatting, drafting, structuring - and it ate the time for the 20% that needed judgment.",
    "Usage-based & per-seat pricing": "Before: flat contracts that priced small teams out and gave big teams no reason to grow into the product.",
    "Open source & community": "Before: black-box software you couldn't inspect, extend, or escape from when the vendor died or raised prices.",
    "Retention by friction": "Before: nothing - and even the companies doing this honestly still lost users to simple forgetfulness.",
}
