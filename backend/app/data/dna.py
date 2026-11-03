"""Product DNA KB (Tab 15 backbone): the philosophy + psychology behind
product patterns, in plain words.

Each PATTERN entry maps observable product language (feature/release text) to:
  philosophy   - why a company builds this (the design belief)
  psychology   - the named principles doing the work, each explained plainly
  business     - the money mechanism + the term for it
  refine       - how a founder applies/avoids this in their own idea
Glossaries define every term the tab uses, so nobody gets lost.
"""
from __future__ import annotations

Pattern = dict

# keyword groups (lowercase, matched against feature text)
PATTERNS: list[Pattern] = [
    {
        "name": "Freemium / free tier",
        "kw": ["free tier", "freemium", "free plan", "free forever", "free up to"],
        "philosophy": "Give the product away, charge for scale. The free tier is the marketing department: every free user is a demo, a referral source and a data point, and it costs the company almost nothing to serve one more.",
        "psychology": [
            ("Foot-in-the-door", "saying yes to 'free' is effortless, and people who said one yes tend to say the next yes (commitment & consistency)."),
            ("Ownership bias", "once your projects/data live inside it, leaving feels like losing something you own."),
        ],
        "business": "Freemium conversion: the % of free users who upgrade pays the whole bill. Works when the marginal cost of a free user is near zero.",
        "refine": "Your free tier must map to something that costs you ~nothing to serve, and the paywall must sit on a value trigger users hit naturally (seats, history, scale), not on random features.",
    },
    {
        "name": "Streaks & habit mechanics",
        "kw": ["streak", "daily challenge", "habit", "check-in", "daily goal", "gamif"],
        "philosophy": "Habit beats marketing. A user who opens the app daily was acquired once and pays forever in attention, so the roadmap optimizes for the second open, not the first.",
        "psychology": [
            ("Loss aversion", "a 47-day streak feels like property; losing it hurts more than gaining a day feels good."),
            ("Variable reward", "not knowing exactly what today's session brings keeps the loop interesting."),
        ],
        "business": "This is a retention mechanism: DAU/WAU and cohort retention are the numbers it moves, and retention is the multiplier on everything else.",
        "refine": "Streaks only fit products with a natural daily moment. A payroll tool with fake streaks is a gimmick; find your product's real frequency first.",
    },
    {
        "name": "Onboarding checklists & progress bars",
        "kw": ["onboarding", "checklist", "getting started", "setup wizard", "progress bar", "guided setup"],
        "philosophy": "Activation before growth. Nothing else matters if the user never reaches the moment the product clicks, so the first session is engineered step by step.",
        "psychology": [
            ("Goal-gradient effect", "people speed up as they see the finish line; a 4/6 checklist pulls them forward."),
            ("Zeigarnik effect", "unfinished tasks nag at the mind; an incomplete checklist literally itches."),
        ],
        "business": "This moves activation rate and time-to-value (TTFV), the metrics that decide whether free users ever convert.",
        "refine": "Define your product's one 'aha' action, then design the shortest honest path to it and show progress toward it. Delete onboarding steps before adding them.",
    },
    {
        "name": "Notifications & digests",
        "kw": ["notification", "push alert", "email digest", "reminder", "re-engag"],
        "philosophy": "Rent attention instead of buying it. The product leaves the browser and comes to the user, so the daily return doesn't depend on the user remembering it exists.",
        "psychology": [
            ("Variable reward", "sometimes the notification is exciting, sometimes not; the unpredictability is what pulls the tap."),
            ("FOMO", "'someone mentioned you' is a social debt you feel you must settle now."),
        ],
        "business": "Re-engagement: notifications cheaply reactivate users who would otherwise churn. Done badly they train users to disable them.",
        "refine": "One notification per user action that genuinely matters beats five per day. Notification permission is a privilege; spam is how you lose it forever.",
    },
    {
        "name": "Referrals & invites",
        "kw": ["referral", "invite", "share with", "refer a friend", "give get"],
        "philosophy": "Users are the channel. If the product is better with more people, make every user a salesperson and pay them in product, not cash.",
        "psychology": [
            ("Social currency", "inviting friends makes the inviter look good for finding the tool first."),
            ("Reciprocity", "'give $10, get $10' starts a relationship with a gift, and people repay gifts."),
        ],
        "business": "Viral coefficient (k): how many new users each user brings. k > 1 means free growth; even k = 0.2 slashes blended CAC.",
        "refine": "Referrals fit products that are naturally better shared (teams, marketplaces). If your product is a solo tool, referral incentives feel like spam.",
    },
    {
        "name": "Templates & starter content",
        "kw": ["template", "preset", "starter kit", "example project", "library of"],
        "philosophy": "The blank page is the enemy. Users don't want your tool, they want the finished thing; templates sell the finished thing first and the tool second.",
        "psychology": [
            ("Cognitive load", "starting from an example removes a dozen decisions before the first click."),
            ("Anchoring", "the template sets what 'done' looks like, and users adapt it rather than question it."),
        ],
        "business": "Activation and time-to-value again: templates are the cheapest activation lift a product can ship.",
        "refine": "Build templates from the top 3 real jobs users hire your product for, not from what looks good in a demo.",
    },
    {
        "name": "Integrations & ecosystem",
        "kw": ["integration", "connect your", "sync with", "marketplace", "api access", "zapier", "webhook"],
        "philosophy": "Live where the user already works. Every integration removes one reason to leave and adds one thread tying the product into the user's daily stack.",
        "psychology": [
            ("Switching costs", "after 6 integrations, replacing the product means re-plumbing their whole workflow."),
            ("Default bias", "if your tool is bundled/connected where they already are, it becomes the path of least resistance."),
        ],
        "business": "Ecosystem moat + expansion revenue: integrations justify higher tiers and make churn expensive for the customer, not just sad.",
        "refine": "Integrate with the 2 tools your users already pay for, not the 20 that look good on a roadmap slide.",
    },
    {
        "name": "Enterprise controls (SSO, audit, roles)",
        "kw": ["sso", "saml", "scim", "audit log", "role-based", "rbac", "admin console", "soc 2", "compliance cert", "data residency"],
        "philosophy": "Charge for trust, not features. Enterprises cannot buy a product their security team hasn't approved, so the approval checklist becomes the price list.",
        "psychology": [
            ("Authority bias", "SOC 2 / ISO badges are borrowed credibility from an institution the buyer already trusts."),
            ("Risk aversion", "the buyer's fear of being blamed for a breach outweighs their desire for a better product."),
        ],
        "business": "This is expansion revenue and higher ACV: the same product sells for 5-20x per seat once the buyer is a company with procurement.",
        "refine": "Enterprise controls are a v2+ move. Ship them when a paying customer literally asks in writing, not before.",
    },
    {
        "name": "Urgency & scarcity mechanics",
        "kw": ["limited time", "only", "expires", "exclusive", "early access", "waitlist", "countdown"],
        "philosophy": "A decision today is worth ten decisions later. Compressing the decision window is how launches convert fence-sitters.",
        "psychology": [
            ("Scarcity", "things that are running out feel more valuable than identical things in stock."),
            ("Loss framing", "'you lose access Friday' moves people more than 'you gain access today'."),
        ],
        "business": "Trial-to-paid conversion lift at the moment of the paywall. Overused, it teaches users your deadlines are fiction.",
        "refine": "Use real deadlines with real reasons (price rises after the first 100, beta ends at capacity). Fake urgency is a brand tax.",
    },
    {
        "name": "Social proof surfaces",
        "kw": ["testimonial", "trusted by", "review", "rating", "case study", "customers love", "logo wall"],
        "philosophy": "Borrowed trust scales. A stranger's endorsement converts better than anything the company can say about itself.",
        "psychology": [
            ("Social proof", "when uncertain, people copy people like them; 'used by 4,000 HR teams' answers 'is this for me?'"),
            ("Authority bias", "a known logo transfers its reputation to your product."),
        ],
        "business": "Pure conversion-rate mechanics on the landing and paywall pages; costs nothing once the customers exist.",
        "refine": "Specific beats big: 'cut onboarding from 3 weeks to 4 days at Acme' outsells 'trusted by thousands'.",
    },
    {
        "name": "Personalization & recommendations",
        "kw": ["personaliz", "recommend", "for you", "smart suggest", "ai-powered", "custom feed"],
        "philosophy": "Relevance is retention. Every irrelevant thing shown is a small tax on attention; a product that knows you removes the tax.",
        "psychology": [
            ("Endowment effect", "a feed tuned to you becomes YOUR feed; leaving means abandoning it."),
            ("Choice architecture", "what gets recommended shapes what gets chosen."),
        ],
        "business": "Retention and engagement lift, which compounds into LTV. Also the classic upsell surface (AI features on premium tiers).",
        "refine": "Personalize only after you have real behavioral data; cold-start 'personalization' that guesses wrong destroys more trust than it builds.",
    },
    {
        "name": "AI copilots & auto-magic",
        "kw": ["ai", "copilot", "auto-generat", "smart compose", "summariz", "assistant", "gpt", "llm"],
        "philosophy": "Delete labor, not add features. The pitch is that the boring 80% of the task happens by itself and the human keeps the judgment calls.",
        "psychology": [
            ("Effort heuristic", "things that took visible effort feel more valuable; 'AI did it in 3 seconds' resets that expectation."),
            ("Automation bias", "people over-trust machine output; the best copilots show their work and keep the human in charge."),
        ],
        "business": "Perceived value per dollar of compute: the margin question (what does inference cost per user per month?) decides if this is a feature or a business.",
        "refine": "Attach AI to the most repetitive step in your workflow, and make the output editable. Full-auto output that's occasionally wrong is worse than draft-plus-human.",
    },
    {
        "name": "Usage-based & per-seat pricing",
        "kw": ["per seat", "per user", "usage-based", "pay as you go", "metered", "per month billed"],
        "philosophy": "Price scales with the value received. The customer who gets 10x the value pays 10x, which feels fair and funds the small customer's free ride.",
        "psychology": [
            ("Fairness perception", "'we pay for what we use' rarely feels exploitative, unlike flat hikes."),
            ("Pain-of-paying calibration", "small frequent charges vs one big invoice changes how expensive the product feels."),
        ],
        "business": "ARPA and expansion revenue: revenue grows automatically as the customer grows, the best kind of sales motion (zero-touch upsell).",
        "refine": "Pick the unit that tracks customer success (seats, records, runs). If your unit punishes success, customers will resent every win.",
    },
    {
        "name": "Open source & community",
        "kw": ["open source", "open-source", "community", "self-host", "contributor", "star us"],
        "philosophy": "Distribution through developers. Give the code away, win the trust of the people who decide what gets installed, and monetize the hosted/managed version.",
        "psychology": [
            ("Reciprocity", "free, useful code creates a debt feeling that translates into adoption and goodwill."),
            ("Status", "contributors earn reputation, which recruits more contributors."),
        ],
        "business": "Product-led growth: the free/open core is the sales team, and the paid tier is convenience (hosting, support, SSO).",
        "refine": "Open source the part that builds trust (the engine), keep the operationally hard part (hosting, compliance) as the business.",
    },
    {
        "name": "Retention by friction",
        "kw": ["cancel flow", "hard to cancel", "retain offer", "save offer", "confirm cancellation"],
        "philosophy": "Retention by friction: make leaving cost more effort than staying. It works in the quarter it's measured and costs brand trust for years.",
        "psychology": [
            ("Default bias", "the option you must actively undo is the one most people keep."),
            ("Friction as tax", "every extra click in the cancel flow recovers some churners and enrages the rest."),
        ],
        "business": "Short-term churn reduction, long-term NPS and review damage. The reviews remember what the dashboard forgets.",
        "refine": "Keep cancellations easy and put the effort into an exit interview plus a one-click 'pause instead'. You learn more and insult less.",
    },
]

# plain-language glossaries. every term used above must be defined here.
BUSINESS_GLOSSARY = {
    "CAC": "Customer Acquisition Cost - what it costs you (money + effort) to get one paying customer.",
    "LTV": "Lifetime Value - total profit one customer generates before they leave.",
    "ARPA": "Average Revenue per Account - what a typical customer pays you per period.",
    "MRR / ARR": "Monthly / Annual Recurring Revenue - the predictable part of your revenue.",
    "Churn": "The % of customers (or revenue) you lose each period. Retention's evil twin.",
    "NRR": "Net Revenue Retention - if existing customers spend more over a year than they churn away, NRR > 100% and growth compounds without new sales.",
    "Payback period": "How many months of revenue it takes to recover one customer's acquisition cost.",
    "Activation rate": "% of new users who reach the moment the product's value actually clicks for them.",
    "Time-to-value (TTFV)": "How long it takes a new user to get their first real result.",
    "TAM / SAM / SOM": "Total / Serviceable / Obtainable market: everyone who could pay, the slice you can serve, the slice you can realistically win.",
    "Moat": "The thing that stops competitors from copying you: data, network, switching costs, brand, regulation.",
    "Switching cost": "What a customer loses (time, data, money, re-learning) if they leave you for a competitor.",
    "Network effect": "The product gets better when more people use it, so growth feeds itself.",
    "Land-and-expand": "Start small inside a company, grow the account over time (more seats, more modules).",
    "Product-led growth (PLG)": "The product itself is the sales channel: free tier or self-serve trial converts users without salespeople.",
    "Freemium conversion": "% of free users who ever pay. Typically 2-5%; the free tier's job is reach, not revenue.",
    "ACV": "Annual Contract Value - what one business customer pays per year.",
    "Viral coefficient (k)": "How many new users one user brings, on average. Above 1 = self-sustaining growth.",
    "Expansion revenue": "Extra revenue from existing customers as they grow (seats, usage, tiers) - the cheapest revenue there is.",
    "Unit economics": "The profit on ONE customer or ONE unit: does the math work before you scale it?",
    "Gross margin": "Revenue minus the direct cost of delivering the service. Decides how much is left to grow with.",
}

PSYCH_GLOSSARY = {
    "Loss aversion": "Losing something hurts roughly twice as much as gaining the same thing feels good.",
    "Variable reward": "Unpredictable rewards hold attention better than predictable ones (the slot-machine effect).",
    "Zeigarnik effect": "Unfinished tasks occupy the mind more than finished ones; that's why progress bars nag.",
    "Goal-gradient effect": "People accelerate as they get closer to a goal.",
    "Default bias": "Whatever requires no action is what most people end up with.",
    "Social proof": "When unsure, people copy what similar people are doing.",
    "Authority bias": "Badges, certifications and expert names transfer trust from the institution to you.",
    "Endowment effect": "People value things more once they feel ownership of them.",
    "Commitment & consistency": "People who take one small step try to stay consistent with it by taking the next ones.",
    "Reciprocity": "A gift (even free value) creates a pull to give back.",
    "Choice architecture": "How options are presented changes which one people pick, without changing the options.",
    "FOMO": "Fear of missing out - social pressure from imagining others getting something you're not.",
    "Cognitive load": "How much thinking a task demands; less load = more completion.",
    "Automation bias": "The tendency to over-trust automated output and skip double-checking it.",
    "Pain of paying": "The psychological discomfort of spending; its intensity depends on how and when payment happens.",
}
