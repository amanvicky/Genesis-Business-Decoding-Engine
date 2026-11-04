"""Founder School KB (Tab 15): the knowledge transfer.

Written as the curriculum someone who has been through zero -> scale would
teach a first-time builder starting from absolute zero: the mental models,
the money mechanics, the vocabulary, the psychology, the order of operations.
Plain language throughout - every term is defined where it first appears.
Personalization: the agent substitutes the founder's own report numbers into
the money lessons, so the teaching is concrete, not theoretical.
"""
from __future__ import annotations

Lesson = dict

PHASES: list[dict] = [
    {
        "phase": 1,
        "name": "The ground truth (what a startup actually is)",
        "why": "Most first-time builders fail because they believe the wrong definition of the job.",
        "lesson_ids": ["what_is_a_startup", "ideas_are_cheap", "buy_information", "oxygen"],
    },
    {
        "phase": 2,
        "name": "Money mechanics (how businesses actually pay you back)",
        "why": "Everything in business is downstream of one equation. Learn it with small numbers first.",
        "lesson_ids": ["the_one_equation", "cac_ltv", "recurring_revenue", "margins"],
    },
    {
        "phase": 3,
        "name": "The user (people don't behave the way you expect)",
        "why": "Products fail because builders trust their own head over other people's behavior.",
        "lesson_ids": ["pain_vs_vitamin", "users_lie", "positioning"],
    },
    {
        "phase": 4,
        "name": "Getting customers with no money",
        "why": "Distribution is the part nobody teaches and everything dies without.",
        "lesson_ids": ["distribution_first", "first_ten"],
    },
    {
        "phase": 5,
        "name": "The machine (running the thing day to day)",
        "why": "Startups don't die of starvation, they die of indigestion - too much at once.",
        "lesson_ids": ["runway_discipline", "hiring_order", "founder_psychology"],
    },
    {
        "phase": 6,
        "name": "The money game (other people's money)",
        "why": "Fundraising is optional, and treating it as mandatory kills more companies than underfunding does.",
        "lesson_ids": ["bootstrap_vs_vc", "what_investors_buy"],
    },
]

LESSONS: dict[str, Lesson] = {
    # ---------------- phase 1 ----------------
    "what_is_a_startup": {
        "title": "A startup is not a small company",
        "lesson": (
            "A small shop is a business: known product, known customers, known margins. A startup is "
            "different - it's a temporary organization searching for a repeatable, scalable business model. "
            "Search, not execution. You don't yet know who the customer is, what they'll pay, or which "
            "channel reaches them. Your job is not to build the product perfectly; it's to run the cheapest "
            "possible experiments that answer those three questions in order: WHO, WHAT, HOW."
        ),
        "truth": "If you know exactly what to build, you're not a startup anymore - you're executing. Startups are ambiguity management.",
        "action": "Write down the three riskiest assumptions behind your idea. Every week you should be killing or confirming one of them.",
        "terms": ["unit economics"],
    },
    "ideas_are_cheap": {
        "title": "Ideas are worth almost nothing",
        "lesson": (
            "Every founder falls in love with the idea and protects it in secret. Here's the uncomfortable "
            "math: an idea with no distribution, no team and no proof is worth roughly zero. What has value "
            "is validated demand (people paying or begging), a working distribution channel, and the team's "
            "ability to iterate. Talking about your idea openly will get you feedback worth far more than "
            "the 'theft risk' costs - execution is the moat, not secrecy."
        ),
        "truth": "Your idea has probably been tried. That's not a bad sign - it can mean demand exists and the earlier teams executed wrong.",
        "action": "Tell 10 people your idea this week, in one sentence each. Write down every objection word-for-word.",
        "terms": ["moat", "distribution"],
    },
    "buy_information": {
        "title": "You are buying information, not building software",
        "lesson": (
            "Every week of work should purchase an answer to a question that changes what you do next. "
            "'Will small business owners pay for automated GST filings?' can be answered in a week with a "
            "landing page and 20 conversations - no code. Building first and learning later is the most "
            "expensive possible way to buy information, because you spend months before the first answer."
        ),
        "truth": "Six months of silent building feels like progress and produces exactly one bit of information: does the launch work.",
        "action": "Before any feature, write the question it answers and how you'll know the answer. If you can't, don't build it.",
        "terms": ["activation", "time-to-value (TTFV)"],
    },
    "oxygen": {
        "title": "Runway is oxygen; everything else is downstream",
        "lesson": (
            "Companies don't die from a lack of ideas, they die when the money hits zero. Runway = cash in "
            "the bank divided by monthly burn. Every decision is a runway decision: the fancy office, the "
            "launch party, the extra engineer. A startup with 3 months of runway and 6 months of work left "
            "is a startup in intensive care, no matter how good the product looks."
        ),
        "truth": "Founders who track runway weekly make calmer, better decisions. Founders who avoid looking, panic late.",
        "action": "Know your burn and your runway date right now, to the rupee/dollar. Update it every Monday.",
        "terms": ["MRR / ARR", "payback period"],
    },
    # ---------------- phase 2 ----------------
    "the_one_equation": {
        "title": "The only equation: does one customer make money?",
        "lesson": (
            "Strip a business to its bones: what does one customer cost you to acquire and serve, and what "
            "do they pay you? If one customer brings in more than they cost, scaling mostly works. If not, "
            "scaling multiplies the loss. That's unit economics. It's tempting to say 'we'll figure out "
            "money later' - but the later you check, the more expensive the surprise."
        ),
        "truth": "Revenue is vanity, margin is sanity, cash is reality.",
        "action": "Write your guess: what one customer pays you per month, and what one customer costs you per month. Both are guesses today - that's fine, write them anyway.",
        "terms": ["unit economics", "gross margin", "CAC", "LTV"],
    },
    "cac_ltv": {
        "title": "CAC and LTV: the two numbers that run your life",
        "lesson": (
            "CAC (Customer Acquisition Cost) is what it costs you to get one paying customer - money plus "
            "your time. LTV (Lifetime Value) is the total profit a customer generates before leaving. The "
            "rule of thumb: LTV should be at least 3x CAC, and you should recover CAC within 12 months. "
            "Example with real numbers: if a customer pays ₹1,000/month at 70% margin, they generate ₹700 "
            "month. If it costs you ₹8,400 to acquire them, you recover the spend in 12 months, and every "
            "month they stay after that is profit. If they churn at month 8, you lost money on every one."
        ),
        "truth": "Founders who don't know their CAC are spending money they don't know they're burning.",
        "action": "Compute one honest CAC today: hours spent on outreach x your hourly value + any money spent, divided by customers acquired so far.",
        "terms": ["CAC", "LTV", "payback period", "churn"],
    },
    "recurring_revenue": {
        "title": "Why everyone wants recurring revenue",
        "lesson": (
            "A one-time sale resets your scoreboard to zero every month. A subscription compounds: 100 "
            "customers paying ₹1,000/month is ₹1,00,000 MRR next month too, even if you sell nothing new. "
            "That's why investors pay more for subscription businesses. The flip side: churn (customers "
            "leaving) leaks the bucket constantly. Growth = new sales minus the leak. This is why retention "
            "is worshipped - fixing a leak helps every future month at once."
        ),
        "truth": "A leaking bucket with more water poured in is still a leaking bucket. Retention problems can't be out-sold.",
        "action": "Sketch your revenue as a bucket: what pours in monthly, what leaks out. Estimate your monthly leak %.",
        "terms": ["MRR / ARR", "NRR", "churn", "retention cohort"],
    },
    "margins": {
        "title": "Margin decides how hard everything else will be",
        "lesson": (
            "Gross margin is what's left after the direct cost of serving one customer. Software margins "
            "(70-90%) are why SaaS is loved: serve customer 10,000 for almost free. Services margins (30-50%) "
            "mean every new customer needs humans, so growth needs hiring. Hardware is worse still. None of "
            "these are wrong - but margin shapes which growth tactics can even work, so know yours early."
        ),
        "truth": "Low margin isn't a death sentence, but it means every growth plan needs more capital than you think.",
        "action": "Estimate your gross margin: monthly revenue minus hosting/tools/support cost per customer, divided by revenue.",
        "terms": ["gross margin", "unit economics"],
    },
    # ---------------- phase 3 ----------------
    "pain_vs_vitamin": {
        "title": "Painkiller vs vitamin",
        "lesson": (
            "A painkiller solves a problem someone has THIS WEEK and already spends money or hours on. A "
            "vitamin is nice-to-have - people agree it's good and then don't buy it. Vitamin products can "
            "win, but only with enormous marketing muscle you don't have. The strongest signal of a "
            "painkiller: people are currently solving the problem badly and hate it - spreadsheets, manual "
            "work, duct-taped tools. You want to find the duct tape."
        ),
        "truth": "'Everyone would want this' is the sound of a vitamin. 'These 5 people already pay someone badly for this' is a painkiller.",
        "action": "Find what your target users currently use instead of your product. If the answer is 'nothing', be worried, not excited.",
        "terms": ["activation", "switching cost"],
    },
    "users_lie": {
        "title": "Users lie (kindly)",
        "lesson": (
            "Ask 'would you use this?' and people say yes to be nice. Ask 'will you pay?' and they say "
            "'definitely!' and never pay. The only honest signals are behavior: money paid, time invested, "
            "referrals given. Ask about the past ('when did this problem last bite you? what did you do?') "
            "not the future ('would you...'). Future questions collect polite fiction."
        ),
        "truth": "Compliments are dangerous. Paid pilots are the only applause that counts.",
        "action": "Replace one 'would you' question with 'when did you last do this manually, walk me through it'.",
        "terms": ["painkiller", "activation"],
    },
    "positioning": {
        "title": "'Better' loses to 'different'",
        "lesson": (
            "You cannot out-feature an incumbent on their axis - they have more engineers and you'll always "
            "look 80% as good. You win by being different on an axis they can't copy: a different customer "
            "(SMBs vs enterprises), a different model (self-serve vs sales-led), a different philosophy "
            "(simple vs powerful). Positioning is choosing what you will be WORSE at on purpose, so you can "
            "be 10x better somewhere that matters to a specific group."
        ),
        "truth": "If your pitch starts with 'like X but better', you've already lost the sale and the margin.",
        "action": "Fill in: 'We are the only [category] for [specific customer] that [unique thing]'. If 'unique thing' is just 'easier', dig deeper.",
        "terms": ["moat", "switching cost"],
    },
    # ---------------- phase 4 ----------------
    "distribution_first": {
        "title": "Distribution is the product's twin",
        "lesson": (
            "The silent killer: great product, zero users, because distribution was an afterthought. Pick "
            "TWO channels - one compounding (SEO, content, open source) and one direct (communities, cold "
            "outreach) - and run them like experiments with weekly scoreboards. Channels have personalities: "
            "SEO takes 6 months and compounds; communities work in weeks and don't scale; paid ads are the "
            "fastest and the most expensive. Match the channel to how your customers already look for solutions."
        ),
        "truth": "No product is so good that it sells itself. That sentence is said by people whose customers market for them.",
        "action": "Name the exact place (subreddit, forum, directory, event) where your future customers already hang out. Go there this week with value, not a pitch.",
        "terms": ["CAC", "product-led growth (PLG)"],
    },
    "first_ten": {
        "title": "The first ten customers are hand-to-hand combat",
        "lesson": (
            "The first 10 customers don't come from marketing. They come from a list of 30 named people, "
            "10 conversations a day, honest demos, and asking for the sale at half price. You will get 90% "
            "silence and that is normal. Each 'no' teaches you the words customers actually use, which "
            "becomes your landing page. This phase cannot be automated, delegated, or skipped - it's where "
            "founders learn what they're actually selling."
        ),
        "truth": "If you can't name 30 specific potential customers, the problem isn't the outreach - it's that you haven't chosen a customer yet.",
        "action": "Today: write 30 names. Not categories - names, companies, or handles.",
        "terms": ["CAC", "activation"],
    },
    # ---------------- phase 5 ----------------
    "runway_discipline": {
        "title": "Runway discipline beats fundraising heroics",
        "lesson": (
            "The startups that survive aren't the best funded - they're the ones whose burn matches their "
            "stage. Two rules keep you alive: (1) founders pay themselves below market, and treat the "
            "saved runway as purchased learning time; (2) spend follows proof - each new cost should trail "
            "a validated win, not precede a hoped one. Contractors before employees. Usage-based "
            "infrastructure before reserved capacity. Every fixed cost converts tomorrow's flexibility "
            "into today's speed only if demand is already proven."
        ),
        "truth": "Most 'we ran out of money' stories are really 'we bought fixed costs before demand justified them'.",
        "action": "List every monthly cost and tag it: PROVEN (trails revenue) or FAITH (hopes revenue). Cut one FAITH cost this month.",
        "terms": ["payback period", "MRR / ARR"],
    },
    "hiring_order": {
        "title": "The hiring order nobody follows",
        "lesson": (
            "Hire in this order: (1) a co-founder whose skills cover your blind spots, (2) contractors for "
            "burst work, (3) your first employee only when a role is drowning in validated, repetitive work "
            "- ideally revenue or retention related. Hiring to feel legitimate, to keep up with peers, or "
            "to do work you haven't validated yet is how burn doubles while learning stays flat. Every "
            "hire should free the founders for the two things only founders can do: talking to customers "
            "and building the core."
        ),
        "truth": "Your first 5 hires define the culture; your first bad hire defines the next 6 months.",
        "action": "Write the one role that would most increase learning speed per rupee. Hire nothing ahead of it.",
        "terms": ["payback period"],
    },
    "founder_psychology": {
        "title": "The psychology nobody warns you about",
        "lesson": (
            "The founder ride has a shape: irrational euphoria at the idea, despair at the first 'no', "
            "false confidence at the first yes, and long flat plateaus where nothing moves. All of it is "
            "normal. Three habits keep you sane: (1) separate your self-worth from the company's weekly "
            "metrics - you are the decision-maker, not the scoreboard; (2) keep a decision journal - "
            "reversible vs irreversible decisions deserve different speeds; (3) define kill criteria "
            "BEFORE you're emotionally inside the product, because future-you will want to move the "
            "goalposts. Quitting by pre-agreed criteria is discipline, not failure."
        ),
        "truth": "Comparison is the thief of founder joy - you're comparing your day 4 to someone's day 1,400.",
        "action": "Write your kill criteria now, while you're objective: what evidence, by when, would make you stop or pivot?",
        "terms": ["activation"],
    },
    # ---------------- phase 6 ----------------
    "bootstrap_vs_vc": {
        "title": "Bootstrap or VC: pick your poison knowingly",
        "lesson": (
            "Raising money is not winning - it's swapping equity for speed with a stranger's goals attached. "
            "Bootstrap (fund it yourself, grow from revenue) keeps control and discipline, and works when "
            "the business can reach positive unit economics early. VC makes sense when the market is huge, "
            "speed decides the winner, and you'd spend investor money on the same things anyway. The worst "
            "place is the middle: raising a little, spending it like a lot. And remember what dilution "
            "really means: every round is a permanent haircut of your ownership, priced by someone betting "
            "on your future."
        ),
        "truth": "VC is rocket fuel AND a timer: raised money must compound into growth, or the timer finds you.",
        "action": "Decide which game you're playing this year: revenue-funded (control, slower) or investor-funded (speed, dilution, external pressure). Write one sentence why.",
        "terms": ["TAM / SAM / SOM", "NRR", "payback period"],
    },
    "what_investors_buy": {
        "title": "What investors actually buy",
        "lesson": (
            "Investors don't buy your product - they buy a slice of a FUTURE company, so they evaluate the "
            "things that predict that future: market size (is the ceiling high?), evidence of demand (are "
            "people paying or begging?), retention (do they stay?), the team (can you learn faster than "
            "others?), and distribution (is there a repeatable way to grow?). Notice: your product is one "
            "input among many. This is why the dossier's tabs map almost one-to-one to an investor's "
            "question list - the research you already have IS the diligence pack."
        ),
        "truth": "Investors fund momentum and evidence, not potential alone. Every month of real usage data is worth more than any deck.",
        "action": "Re-read your dossier as an investor would. Which tab would YOU attack first? That's your weak flank - fix it before anyone else sees it.",
        "terms": ["TAM / SAM / SOM", "NRR", "unit economics"],
    },
}
