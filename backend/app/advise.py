"""Real-time advisor: answers questions using the dossier's own numbers.

Deterministic intent routing over the report, no LLM needed. Streams NDJSON:
  {"type": "log", "msg": "..."}                     reasoning trail
  {"type": "answer", "answer": str, "bullets": [...],
   "open_tabs": ["financial", ...], "followups": ["..."]}
"""
from __future__ import annotations

import re
from typing import Any

MAX_QUESTION = 500

# teaching index: every glossary term + lesson title, so "what is churn" or
# "explain CAC" routes to the school before any other intent
_TERM_INDEX: set[str] = set()


def _build_term_index() -> None:
    from .data.dna import BUSINESS_GLOSSARY, PSYCH_GLOSSARY
    from .data.school import LESSONS
    for t in list(BUSINESS_GLOSSARY) + list(PSYCH_GLOSSARY):
        for a in t.replace("(", "").split(" / "):
            _TERM_INDEX.add(a.strip().lower())
    for l in LESSONS.values():
        for w in re.findall(r"[a-z]{4,}", l["title"].lower()):
            if w not in ("with", "your", "that", "nobody", "follows", "warning"):
                _TERM_INDEX.add(w)


_build_term_index()

Intent = str


def detect_intent(question: str) -> Intent:
    q = f" {question.lower().strip()} "
    if re.search(r"\b(hi|hello|hey|help|what can you)\b", q) and len(q.strip()) < 30:
        return "hello"
    # "what is churn" / "explain CAC" where the X is a business or psychology
    # term: that's the founder school teaching, and it must win before keyword
    # intents (or "what is runway" would hit the burn rule instead of the lesson)
    m = re.search(r"\b(?:what (?:is|are)|what's|explain|meaning of|define|teach me(?: about)?)\s+(?:the |a |an )?(?P<term>[a-z][\w -]{2,38})", q)
    if m:
        words = m.group("term").split()
        # "what is MY burn" is a dossier question, not a definition request
        if words and words[0] in ("my", "our", "your"):
            pass
        elif any(w in _TERM_INDEX for w in words) or m.group("term").strip() in _TERM_INDEX:
            return "teach"
    rules: list[tuple[Intent, str]] = [
        # red-team first: "what will investors SAY" is an objection question,
        # not a capital question — the say/ask context decides
        ("redteam", r"\b(objection|pitch|red team|red-team|weakness|investors? (say|will say|would say|ask))\b"),
        ("teach", r"\b(teach me|explain like|knowledge transfer|founder school|new to (business|startups|this)|first[- ]time founder|learn (the )?basics|how (do|does) (start-?ups|startups|businesses?|saas|funding) work)\b"),
        ("markets", r"\b(stock (price|performance)|share price|how (is|did) the stock|rises? and falls?|listed|publicly traded)\b"),
        ("deepdive", r"\b(how (did|do|does) (they|the company|this company)|what (do|does|did) (they|the company|this company) (do|sell|make|offer)|their marketing|the company'?s marketing|how (did|do) they (market|promote|start|grow|begin|acquire|win)|company (story|origin|history)|origin (story|of the)|reality check|things (i('| i)?ll|to) (face|consider|come across)|what will i (come|face)|feature (breakdown|inventory)|every (single )?(feature|option)|all (of )?the (features|options))\b"),
        ("dna", r"\b(philosoph\w*|psycholog\w*|product dna|explain (the |this |that )?\w*( feature| product| pattern| pricing| design)|why (does|did|is) (this|that|their|it)\b|how (does|did) [a-z ]{3,30} work)\b"),
        ("capital", r"\b(raise|funding|invest|dilut|bootstrap|valuation|cap\b|safe|equity|money)\w*"),
        ("market", r"\b(tam|sam|som)\b|\bmarket(ing| size)?\b|big enough"),
        ("competitors", r"\b(competitor|alternative|who else|rival|existing|already does)\w*"),
        ("mvp", r"\b(mvp|build first|what (should|do) i build|feature|roadmap|sequence|scope)\w*"),
        ("compliance", r"\b(compliance|legal|licen[cs]e|regulat|gst|epf|esi|law|tax registration)\w*"),
        ("pricing", r"\b(pric|charge|arpa|tier|how much (should|can) i charge)\w*"),
        ("burn", r"\b(burn|runway|breakeven|break-even|cost|salary|expenses)\w*"),
        ("customers", r"\b(first (10|ten|customers)|acquire|acquisition|distribution|marketing|grow|users)\w*"),
        ("risk", r"\b(fail|kill|risk|die|death|wrong|premortem|post-mortem)\w*"),
    ]
    for intent, pattern in rules:
        if re.search(pattern, q):
            return intent
    return "next"


def _num(v: Any, currency: str = "$") -> str:
    if v is None:
        return "—"
    try:
        n = float(v)
    except (TypeError, ValueError):
        return str(v)
    if currency == "₹":
        if abs(n) >= 1e7:
            return f"₹{n / 1e7:,.1f}Cr"
        if abs(n) >= 1e5:
            return f"₹{n / 1e5:,.1f}L"
        return f"₹{n:,.0f}"
    if abs(n) >= 1e9:
        return f"${n / 1e9:,.1f}B"
    if abs(n) >= 1e6:
        return f"${n / 1e6:,.1f}M"
    return f"${n:,.0f}"


def _section(report: dict, sid: str) -> dict:
    return ((report.get("sections") or {}).get(sid) or {}).get("data") or {}


def _subject(report: dict) -> str:
    return str(report.get("subject") or "your idea")


def advise(question: str, report: dict) -> dict:
    """Route the question to the dossier's own numbers. Pure function."""
    q = (question or "").strip()[:MAX_QUESTION]
    intent = detect_intent(q)
    handler = _HANDLERS.get(intent, _advise_next)
    return handler(q, report)


# ------------------------------------------------------------------ handlers

def _advise_hello(q: str, report: dict) -> dict:
    return {
        "answer": (
            f"I'm Genesis — I already decoded {_subject(report)} into a 14-tab dossier. "
            "Ask me anything in it: numbers, decisions, next steps. I answer from YOUR report, not generic advice."
        ),
        "bullets": [
            "“Should I raise or bootstrap?” — capital math from your burn + market base",
            "“What do I build first?” — your MVP sequence and bloat gates",
            "“Who already does this?” — the alternatives scan",
            "“What kills companies like this?” — your matched failure records",
        ],
        "open_tabs": [],
        "followups": ["Should I raise or bootstrap?", "What do I build first?", "What's my biggest risk?"],
    }


def _advise_capital(q: str, report: dict) -> dict:
    fin = _section(report, "financial").get("computed") or {}
    ms = _section(report, "marketsize")
    cap = ms.get("capital_strategy") or {}
    geo = ((report.get("request") or {}).get("geography") or "")
    cur = (ms.get("assumptions") or {}).get("currency") or ("₹" if geo == "india" else "$")
    burn = fin.get("burn_month")
    raise_amt = cap.get("recommended_raise")
    dil = cap.get("dilution_at_geo_cap_pct")
    if not raise_amt:
        return {
            "answer": "I can't give capital math without your burn numbers — the financial tab hasn't computed yet. Re-run the decode.",
            "bullets": [], "open_tabs": ["financial", "marketsize"], "followups": ["What's my burn?"],
        }
    bullets = [
        f"Recommended raise: {_num(raise_amt, cur)} = burn ({_num(burn, cur)}/mo) × 18 months × 1.25 buffer.",
        f"Dilution: ≈{dil}% at the geo-typical pre-seed cap ({cap.get('dilution_formula')}).",
        f"Timing: {cap.get('raise_when')}",
        cap.get("bootstrap_note", ""),
    ]
    return {
        "answer": f"Raise {_num(raise_amt, cur)} — but only after gate G1. Here's the math:",
        "bullets": [b for b in bullets if b],
        "open_tabs": ["marketsize", "financial"],
        "followups": ["What's my dilution at other caps?", "Can I bootstrap instead?", "When exactly is gate G1?"],
    }


def _advise_market(q: str, report: dict) -> dict:
    ms = _section(report, "marketsize")
    if not ms:
        return {"answer": "No market sizing in this report yet — re-run the decode.", "bullets": [], "open_tabs": ["marketsize"], "followups": []}
    tam, sam = ms.get("tam") or {}, ms.get("sam") or {}
    som = (ms.get("som_by_year") or [{}])[-1]
    return {
        "answer": str(ms.get("verdict") or "Sizing incomplete."),
        "bullets": [
            f"TAM {tam.get('display')} — {tam.get('basis')}",
            f"SAM (your wedge) {sam.get('display')} — {sam.get('basis')}",
            f"3-year SOM {som.get('display')} at {som.get('adoption')} earned adoption ({som.get('customers'):,} customers).",
            "Every figure is bottom-up and editable — the ARPA comes from your pricing sandbox.",
        ],
        "open_tabs": ["marketsize", "pricing"],
        "followups": ["Is my market big enough?", "What's my SOM in year 1?", "Should I raise or bootstrap?"],
    }


def _advise_competitors(q: str, report: dict) -> dict:
    feats = _section(report, "features")
    alts = feats.get("alternatives") or {}
    candidates = alts.get("candidates") or []
    chatter = alts.get("chatter") or []
    if not candidates and not chatter:
        return {
            "answer": (
                f"The evidence scan found no named alternatives for {_subject(report)} — either the niche is thin online, "
                "or you're early. That's a signal to interview, not a proof of blue ocean: search the exact pain phrase yourself."
            ),
            "bullets": ["No competitor is ALSO a risk: 'nobody does this' usually means 'nobody searched this'."],
            "open_tabs": ["features"],
            "followups": ["What do I build first?", "How do I find my first 10 customers?"],
        }
    bullets = [f"Named in live evidence: {', '.join(candidates[:6])}"] if candidates else []
    bullets += [f"“{c['text'][:120]}…” — {c['url']}" for c in chatter[:3]]
    bullets.append("Verify each by using their product as a customer. Note what they charge and what users complain about.")
    return {
        "answer": f"{len(candidates)} candidate alternative(s) surfaced for {_subject(report)} — mined from live evidence, verify each.",
        "bullets": bullets,
        "open_tabs": ["features"],
        "followups": ["How am I different from them?", "What do I build first?"],
    }


def _advise_mvp(q: str, report: dict) -> dict:
    feats = _section(report, "features")
    seq = feats.get("mvp_sequence") or []
    roadmap = feats.get("binary_roadmap") or {}
    never = roadmap.get("never_for_mvp") or []
    if not seq:
        return {"answer": "No build sequence in this report — re-run the decode.", "bullets": [], "open_tabs": ["features"], "followups": []}
    steps = [f"{s['order']}. {s['build']}" for s in seq[:6]]
    return {
        "answer": "Build in this order — each step only earns its place after the previous one shows signal:",
        "bullets": steps + [f"DO NOT build: {n['feature']} — gate: {n.get('gate', '')}" for n in never[:3]],
        "open_tabs": ["features", "timeline"],
        "followups": ["What's my biggest risk?", "How do I get my first 10 customers?"],
    }


def _advise_compliance(q: str, report: dict) -> dict:
    comp = _section(report, "compliance")
    items = comp.get("checklist") or comp.get("landmines") or []
    critical = comp.get("critical_count") or sum(1 for i in items if "block" in str(i.get("severity", "")).lower())
    if not items:
        return {"answer": "No compliance checklist in this report — re-run the decode.", "bullets": [], "open_tabs": ["compliance"], "followups": []}
    top = [f"{i.get('item', '?')} — {i.get('cost', '?')}, {i.get('time', '?')}" for i in items[:5]]
    return {
        "answer": f"{len(items)} statutory obligations decoded, {critical} are launch-blocking. Start with these:",
        "bullets": top + ["The checklist is ordered — do them in sequence; several have multi-week lead times."],
        "open_tabs": ["compliance"],
        "followups": ["What does compliance cost total?", "What's my biggest risk?"],
    }


def _advise_pricing(q: str, report: dict) -> dict:
    pricing = _section(report, "pricing")
    ue = pricing.get("unit_economics") or {}
    tiers = pricing.get("tiers") or []
    cur = ue.get("currency", "$")
    if tiers:
        lines = [f"{t['name']}: {t['price']}" for t in tiers[:5]]
        return {
            "answer": f"{len(tiers)} tier(s) decoded from live evidence — your unit economics:",
            "bullets": lines + [
                f"LTV {ue.get('ltv')} · LTV:CAC {ue.get('ltv_cac_ratio')} · payback {ue.get('cac_payback_months')} months.",
                "Edit CAC/churn/margin in the sandbox — every number recomputes live.",
            ],
            "open_tabs": ["pricing", "marketsize"],
            "followups": ["Is my market big enough?", "Should I raise or bootstrap?"],
        }
    return {
        "answer": f"No public pricing decoded — you're defining the category. Geography defaults: ARPA {cur}{ue.get('arpa')}.",
        "bullets": [
            "Price from customer #1. A discount expires; a free tier is a permanent COGS line.",
            f"Recommended 3-tier ladder is in Tab 6 — anchor on the middle tier.",
            "The sandbox is live: change ARPA and see breakeven move in Tab 8.",
        ],
        "open_tabs": ["pricing", "financial"],
        "followups": ["What's my burn?", "Is my market big enough?"],
    }


def _advise_burn(q: str, report: dict) -> dict:
    fin = _section(report, "financial")
    comp = fin.get("computed") or {}
    if not comp:
        return {"answer": "No burn model in this report — re-run the decode.", "bullets": [], "open_tabs": ["financial"], "followups": []}
    return {
        "answer": "Your financial reality, as computed:",
        "bullets": [
            f"Burn: {_num(comp.get('burn_month'))}/month (team of {fin.get('team_size', '?')}, geo-adjusted salaries).",
            f"Capital for the {fin.get('runway_target_months', '?')}-month target: {_num(comp.get('capital_needed'))}.",
            f"Breakeven: ~{comp.get('breakeven_customers'):,} customers at ARPA {_num(comp.get('arpa_assumption'))}.",
            "Salary −25% or one fewer engineer moves breakeven more than any pricing tweak — see the sensitivity table.",
        ],
        "open_tabs": ["financial", "marketsize"],
        "followups": ["Should I raise or bootstrap?", "Is my market big enough?"],
    }


def _advise_customers(q: str, report: dict) -> dict:
    dist = _section(report, "distribution")
    channels = dist.get("channels") or []
    first_ten = dist.get("first_ten") or []
    top = [c.get("name", "?") for c in channels[:2]]
    step1 = next((s for s in first_ten if s.get("step") == 1), {})
    return {
        "answer": "Two moves: pick the loop, then run the first-10 plan inside it.",
        "bullets": [
            f"Top-ranked loops for you: {' · '.join(top)}.",
            f"Day 1–3: {step1.get('action', 'List 30 named prospects from the top channel.')}",
            "Day 3–7: contact 10/day, 3 lines, no links. Week 2: 20-minute problem interviews. Week 2–3: paid pilots at 50%.",
            "Day 30 verdict: fewer than 3 paid pilots → the pain or pitch is wrong; 3+ → point the compounding loop at the exact wording that worked.",
        ],
        "open_tabs": ["distribution"],
        "followups": ["Who already does this?", "What do I build first?"],
    }


def _advise_risk(q: str, report: dict) -> dict:
    prem = _section(report, "premortem")
    modes = prem.get("common_failure_modes") or []
    analogs = prem.get("analogs") or []
    adversary = _section(report, "adversary")
    fatal = adversary.get("fatal_count")
    bullets = [f"{m.get('mode', '?')} — counter: {str(m.get('counter', ''))[:150]}" for m in modes[:3]]
    bullets += [
        f"{a.get('name', '?')}: {str(a.get('root_cause', a.get('lesson', '')))[:140]}"
        for a in analogs[:2]
    ]
    if fatal is not None:
        bullets.append(f"Your own red-team panel raised {fatal} FATAL challenges — they're in Tab 14, answer or cut each one.")
    if not bullets:
        bullets = ["Re-run the decode to build the failure and red-team analysis."]
    return {
        "answer": f"What kills companies like {_subject(report)} — from matched post-mortems and your own red-team:",
        "bullets": bullets,
        "open_tabs": ["premortem", "adversary"],
        "followups": ["What do I build first?", "Should I raise or bootstrap?"],
    }


def _advise_redteam(q: str, report: dict) -> dict:
    adv = _section(report, "adversary")
    personas = adv.get("personas") or []
    bullets = []
    for p in personas[:3]:
        role = p.get("role") or p.get("name", "?")
        ch = (p.get("challenges") or [{}])[0]
        bullets.append(f"{role}: {str(ch.get('challenge', ''))[:160]}")
    if not bullets:
        bullets = ["Re-run the decode to generate the three-persona cross-examination."]
    return {
        "answer": "The strongest objections to your plan, from the adversarial panel:",
        "bullets": bullets + ["Fatal gaps must be ANSWERED or the feature/plan CUT — that's the protocol."],
        "open_tabs": ["adversary", "playbook"],
        "followups": ["What's my biggest risk?", "What should I do next?"],
    }


def _advise_next(q: str, report: dict) -> dict:
    """Default: compose the NOW/WEEK-1 decision list from the dossier's own verdicts."""
    struct = _section(report, "structural")
    ms = _section(report, "marketsize")
    comp = _section(report, "compliance")
    now: list[str] = []
    verdict = struct.get("verdict") or ""
    if "UNKNOWN" in verdict:
        now.append("Re-run the decode ONLINE — your current run gathered no evidence, so pain/signal is unmeasured.")
    elif "Weak" in verdict:
        now.append("Signal is weak: 20 problem interviews BEFORE any code. The dossier's pain tables tell you what to ask.")
    else:
        now.append("Signal exists — run the first-10 plan (Tab 9) inside the top-ranked channel this week.")
    critical = comp.get("critical_count")
    if critical:
        now.append(f"Start the compliance clock: {critical} launch-blocking obligations, some take weeks — Tab 3 has the ordered list.")
    msv = ms.get("verdict") or ""
    if "DOESN'T CLOSE" in msv:
        now.append("Your market math doesn't fund this team — fix the wedge/price/team before writing code.")
    adv = _section(report, "adversary")
    if adv.get("fatal_count"):
        now.append(f"Answer the {adv['fatal_count']} fatal red-team challenges — each one is a plan-killer if ignored.")
    return {
        "answer": f"Where {_subject(report)} stands, straight from your dossier:",
        "bullets": now[:4] + ["Ask me anything specific — pricing, competitors, raise, compliance, risks."],
        "open_tabs": ["structural", "marketsize", "compliance"],
        "followups": ["Should I raise or bootstrap?", "Who already does this?", "What kills companies like this?"],
    }


def _advise_dna(q: str, report: dict) -> dict:
    dna = _section(report, "dna")
    if not dna:
        return {"answer": "No Product DNA section in this report yet — re-run the decode to build it.",
                "bullets": [], "open_tabs": ["dna"], "followups": ["What should I do next?"]}

    # did they ask about a specific feature? score features by word overlap
    words = {w.lower() for w in re.findall(r"[a-z]{4,}", q.lower())}
    best, best_score = None, 0
    for fb in dna.get("features") or []:
        fwords = {w.lower() for w in re.findall(r"[a-z]{4,}", fb.get("feature", ""))}
        score = len(words & fwords)
        if score > best_score:
            best, best_score = fb, score

    if best:
        lines = []
        for pat in best.get("patterns", []):
            lines.append(f"Philosophy: {pat['philosophy']}")
            for ps in pat["psychology"]:
                lines.append(f"Psychology ({ps['principle']}): {ps['explained']}")
            lines.append(f"Business: {pat['business']}")
            for po in pat.get("played_out", [])[:1]:
                lines.append(f"How it played out for them: {po['text']}")
            lines.append(f"In the wild: {pat.get('worked', '')}")
            lines.append(f"Steal it: {pat['refine']}")
        return {"answer": f"The breakdown of '{best.get('feature', '')}':",
                "bullets": lines, "open_tabs": ["dna"],
                "followups": ["How do I get my first 10 customers?", "What's my biggest risk?"]}

    phil = dna.get("product_philosophy") or {}
    top = (phil.get("top_patterns") or [{}])[0]
    return {
        "answer": str(phil.get("headline") or "No product philosophy decoded."),
        "bullets": [
            f"{top.get('name', '')} is the dominant pattern: {top.get('philosophy', '')}" if top else "",
            "Ask about any specific feature and I'll break down its philosophy, psychology and business mechanics.",
            "Every term is defined in plain words at the bottom of Tab 14.",
        ][:3],
        "open_tabs": ["dna"],
        "followups": ["What do I build first?", "Who already does this?", "What's my biggest risk?"],
    }



def _advise_markets(q: str, report: dict) -> dict:
    mk = _section(report, "markets")
    if not mk or mk.get("traded") is None:
        return {"answer": "No market performance data in this report (private company, offline run, or lookup failed).",
                "bullets": [], "open_tabs": ["markets"], "followups": ["What should I do next?"]}
    perf = mk.get("performance") or {}
    lines = []
    for w in (perf.get("best_weeks") or [])[:2]:
        lines.append(f"Rose {w['change_pct']:+.1f}% week of {w['date']} ({w['from']} to {w['to']})")
    for w in (perf.get("worst_weeks") or [])[:2]:
        lines.append(f"Fell {w['change_pct']:.1f}% week of {w['date']} ({w['from']} to {w['to']})")
    dd = perf.get("max_drawdown") or {}
    if dd:
        lines.append(f"Worst peak-to-trough drawdown: {dd.get('pct')}% (as of {dd.get('date')})")
    return {"answer": str(mk.get("summary") or ""), "bullets": lines, "open_tabs": ["markets"],
            "followups": ["What's my biggest risk?", "Is my market big enough?"]}


def _advise_deepdive(q: str, report: dict) -> dict:
    """The deep-dive voice: what they do, their features, the reality, their marketing."""
    dd = _section(report, "deepdive")
    if not dd:
        return {"answer": "No deep-dive section in this report yet — re-run the decode to build it.",
                "bullets": [], "open_tabs": ["deepdive"], "followups": ["What should I do next?"]}
    low = q.lower()
    wtd = dd.get("what_they_do") or {}

    # marketing sub-question
    if re.search(r"\b(marketing|promot|audience|market (it|the|their)|acquire)\b", low):
        mk = dd.get("marketing") or {}
        bullets = []
        for m in (mk.get("mechanics") or [])[:4]:
            sig = f" (evidence: {', '.join(m.get('signals', [])[:3])})" if m.get("signals") else ""
            bullets.append(f"{m['mechanic']}{sig} — what they promote: {m['what_they_promote']}. {m['psych']}")
        if mk.get("the_hook"):
            bullets.append(f"The hook: {mk['the_hook']} — the entry surface everything else pulls people through.")
        if mk.get("channel_ranking"):
            bullets.append(f"Top channels for this category: {' · '.join(mk['channel_ranking'])}.")
        return {
            "answer": f"How {_subject(report)} actually reaches people — the concrete mechanics, not the 'they do digital marketing' filler:",
            "bullets": bullets or ["No marketing mechanics were visible in this run's evidence — decode with network for the full picture."],
            "open_tabs": ["deepdive", "distribution"],
            "followups": ["What do they actually do?", "What will I come across building this?"],
        }

    # reality-check sub-question
    if re.search(r"\b(reality|consider|come across|will i face|up against|hidden|truth)\b", low):
        items = (dd.get("reality_check") or {}).get("items") or []
        return {
            "answer": "The reality of building in this space — observations of what actually happens, not instructions:",
            "bullets": [f"{i['area']} — {i['what'][:180]}" for i in items[:5]] or ["No reality checks computed."],
            "open_tabs": ["deepdive", "premortem"],
            "followups": ["How did they market this?", "What do they actually do?"],
        }

    # feature inventory sub-question
    if re.search(r"\b(feature|option|inventory)\b", low):
        inv = dd.get("feature_inventory") or []
        bullets = [
            f"{f['feature']} — before it: {f['the_issue_before'][:120]} impact: {f['the_impact'][:90]}"
            for f in inv[:4]
        ]
        return {
            "answer": f"{len(inv)} features inventoried for {_subject(report)}, each with the issue people had before it, the trigger that produced it, and what it changed:",
            "bullets": bullets or ["No feature inventory in this run — decode with network."],
            "open_tabs": ["deepdive", "features"],
            "followups": ["How did they market this?", "What's the psychology behind their features?"],
        }

    # default: the what-they-do layer
    return {
        "answer": f"What {_subject(report)} actually does:",
        "bullets": [
            f"Problem: {str(wtd.get('the_problem', ''))[:200]}",
            f"Solution: {str(wtd.get('the_solution', ''))[:200]}",
            f"Trigger: {str(wtd.get('the_trigger', ''))[:160]}",
            f"Founder logic: {str(wtd.get('founder_logic', ''))[:160]}",
        ],
        "open_tabs": ["deepdive", "dna"],
        "followups": ["How did they market this?", "What will I come across building this?", "Break down their features"],
    }


def _advise_teach(q: str, report: dict) -> dict:
    """The mentor voice: find the lesson or term the founder is asking about."""
    from .data.dna import BUSINESS_GLOSSARY, PSYCH_GLOSSARY
    from .data.school import LESSONS, PHASES
    low = q.lower()

    # exact glossary term first
    for source, gloss in (("business", BUSINESS_GLOSSARY), ("psychology", PSYCH_GLOSSARY)):
        for term, definition in gloss.items():
            for alias in term.replace("(", "").split(" / "):
                if re.search(rf"\b{re.escape(alias.lower())}\b", low):
                    lesson_hit = next((l for l in LESSONS.values() if alias.lower() in l["lesson"].lower()
                                       or any(alias.lower() in t for t in l.get("terms", []))), None)
                    bullets = [definition, f"Source: the {source} vocabulary in Founder School (Tab 15)."]
                    if lesson_hit:
                        bullets.append(f"The lesson '{lesson_hit['title']}' shows it in context: {lesson_hit['truth']}")
                    return {"answer": f"{term}: {definition}", "bullets": bullets,
                            "open_tabs": ["school"], "followups": ["Teach me the money mechanics", "What kills companies like this?"]}

    # otherwise: best lesson by word overlap (stemmed, title-match boosted)
    def _stem(w: str) -> str:
        return w[:-1] if w.endswith("s") else w

    words = {_stem(w) for w in re.findall(r"[a-z]{4,}", low)} - {"what", "explain", "about", "teach", "like", "understand"}
    phase_of = {lid: ph["phase"] for ph in PHASES for lid in ph["lesson_ids"]}
    best, best_id, best_score = None, "what_is_a_startup", 0
    for lid, l in LESSONS.items():
        text = " ".join(_stem(w) for w in re.findall(r"[a-z]{4,}", (l["title"] + " " + l["lesson"]).lower()))
        score = len(words & set(text.split()))
        if "startup" in lid and any(w in text for w in words):
            score += 2  # "how do startups work" should hit the intro lesson
        if score > best_score:
            best, best_id, best_score = l, lid, score
    followups = [LESSONS[lid]["title"] for lid in phase_of
                 if phase_of[lid] == phase_of[best_id] and lid != best_id][:2]
    return {
        "answer": f"{best['title']}. {best['lesson']}",
        "bullets": [f"The uncomfortable truth: {best['truth']}", f"Do this now: {best['action']}"],
        "open_tabs": ["school"],
        "followups": followups or ["Teach me the money mechanics", "What is a startup really?"],
    }


_HANDLERS = {
    "hello": _advise_hello,
    "capital": _advise_capital,
    "market": _advise_market,
    "competitors": _advise_competitors,
    "mvp": _advise_mvp,
    "compliance": _advise_compliance,
    "pricing": _advise_pricing,
    "burn": _advise_burn,
    "customers": _advise_customers,
    "risk": _advise_risk,
    "redteam": _advise_redteam,
    "dna": _advise_dna,
    "teach": _advise_teach,
    "markets": _advise_markets,
    "deepdive": _advise_deepdive,
    "next": _advise_next,
}
