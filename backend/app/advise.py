"""Real-time advisor: answers questions using the brief's own numbers.

Deterministic intent routing over the report, no LLM needed. Streams NDJSON:
  {"type": "log", "msg": "..."}                     reasoning trail
  {"type": "answer", "answer": str, "bullets": [...],
   "open_tabs": ["deepdive", ...], "followups": ["..."]}
"""
from __future__ import annotations

import re
from typing import Any

MAX_QUESTION = 500

# term index: every dna-tab glossary term, so "what is churn" or "explain CAC"
# routes to a definition before any keyword intent
_TERM_INDEX: set[str] = set()


def _build_term_index() -> None:
    from .data.dna import BUSINESS_GLOSSARY, PSYCH_GLOSSARY
    for t in list(BUSINESS_GLOSSARY) + list(PSYCH_GLOSSARY):
        for a in t.replace("(", "").split(" / "):
            _TERM_INDEX.add(a.strip().lower())


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
        # "what is MY burn" is a brief question, not a definition request
        if words and words[0] in ("my", "our", "your"):
            pass
        elif any(w in _TERM_INDEX for w in words) or m.group("term").strip() in _TERM_INDEX:
            return "teach"
    rules: list[tuple[Intent, str]] = [
        # red-team first: "what will investors SAY" is an objection question,
        # not a capital question — the say/ask context decides
        ("redteam", r"\b(objection|pitch|red team|red-team|weakness|investors? (say|will say|would say|ask))\b"),
        ("teach", r"\b(teach me|explain like|what does .* mean|new to (business|startups|this)|first[- ]time founder|learn (the )?basics)\b"),
        ("markets", r"\b(stock (price|performance)|share price|how (is|did) the stock|rises? and falls?|listed|publicly traded)\b"),
        ("deepdive", r"\b(how (did|do|does) (they|the company|this company)|what (do|does|did) (they|the company|this company) (do|sell|make|offer)|their marketing|the company'?s marketing|how (did|do) they (market|promote|start|grow|begin|acquire|win)|company (story|origin|history)|origin (story|of the)|reality check|things (i('| i)?ll|to) (face|consider|come across)|what will i (come|face)|feature (breakdown|inventory)|every (single )?(feature|option)|all (of )?the (features|options))\b"),
        ("dna", r"\b(philosoph\w*|psycholog\w*|product dna|explain (the |this |that )?\w*( feature| product| pattern| pricing| design)|why (does|did|is) (this|that|their|it)\b|how (does|did) [a-z ]{3,30} work)\b"),
        ("competitors", r"\b(competitor|alternative|who else|rival|existing|already does)\w*"),
        ("mvp", r"\b(mvp|build first|what (should|do) i build|feature|roadmap|sequence|scope)\w*"),
        ("compliance", r"\b(compliance|legal|licen[cs]e|regulat|gst|epf|esi|law|tax registration)\w*"),
        ("pricing", r"\b(pric|charge|arpa|tier|how much (should|can) i charge)\w*"),
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
    """Route the question to the brief's own numbers. Pure function."""
    q = (question or "").strip()[:MAX_QUESTION]
    intent = detect_intent(q)
    handler = _HANDLERS.get(intent, _advise_next)
    return handler(q, report)


# ------------------------------------------------------------------ handlers

def _advise_hello(q: str, report: dict) -> dict:
    return {
        "answer": (
            f"I'm Genesis — I already decoded {_subject(report)} into a 13-tab research brief. "
            "Ask me anything in it: what they do, what users complain about, what it costs them, what's filed. I answer from YOUR report, not generic advice."
        ),
        "bullets": [
            "“What do they actually do?” — the deep-dive",
            "“Who already does this?” — the alternatives scan",
            "“What kills companies like this?” — your matched failure records",
            "“How did they market this?” — the concrete mechanics",
        ],
        "open_tabs": [],
        "followups": ["What do they actually do?", "Who already does this?", "What kills companies like this?"],
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
    tiers = pricing.get("tiers") or []
    if tiers:
        lines = [f"{t['name']}: {t['price']}" for t in tiers[:6]]
        psych = pricing.get("psychology") or []
        lines += [f"{p['driver']}: {p['evidence']}" for p in psych[:2]]
        return {
            "answer": f"{len(tiers)} tier(s) decoded from {(_subject(report))}'s live pricing — what they actually charge:",
            "bullets": lines,
            "open_tabs": ["pricing"],
            "followups": ["What do they actually do?", "Who already does this?"],
        }
    return {
        "answer": f"No public pricing decoded for {_subject(report)} — nothing visible on their site or in the evidence.",
        "bullets": [
            "That absence is itself a fact: quote-based sales, or pricing hidden behind demo gates.",
            "The wayback history (Tab 6) shows what they charged in past years when a snapshot exists.",
        ],
        "open_tabs": ["pricing"],
        "followups": ["What do they actually do?", "Who already does this?"],
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
        bullets.append(f"Your own red-team panel raised {fatal} FATAL challenges — they're in Tab 13, answer or cut each one.")
    if not bullets:
        bullets = ["Re-run the decode to build the failure and red-team analysis."]
    return {
        "answer": f"What kills companies like {_subject(report)} — from matched post-mortems and your own red-team:",
        "bullets": bullets,
        "open_tabs": ["premortem", "adversary"],
        "followups": ["What do I build first?", "What do they actually charge?"],
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
        "open_tabs": ["adversary"],
        "followups": ["What's my biggest risk?", "What should I do next?"],
    }


def _advise_next(q: str, report: dict) -> dict:
    """Default: compose the NOW/WEEK-1 decision list from the brief's own verdicts."""
    struct = _section(report, "structural")
    comp = _section(report, "compliance")
    now: list[str] = []
    verdict = struct.get("verdict") or ""
    if "UNKNOWN" in verdict:
        now.append("Re-run the decode ONLINE — your current run gathered no evidence, so pain/signal is unmeasured.")
    elif "Weak" in verdict:
        now.append("Signal is weak: 20 problem interviews BEFORE any code. The brief's pain tables tell you what to ask.")
    else:
        now.append("Signal exists — the pain is voiced publicly; the deep-dive and features tabs show what users live with today.")
    critical = comp.get("critical_count")
    if critical:
        now.append(f"Compliance weight: {critical} launch-blocking obligations in this sector — Tab 3 has the ordered list.")
    adv = _section(report, "adversary")
    if adv.get("fatal_count"):
        now.append(f"Answer the {adv['fatal_count']} fatal red-team challenges — each one is a plan-killer if ignored.")
    return {
        "answer": f"Where {_subject(report)} stands, straight from your brief:",
        "bullets": now[:4] + ["Ask me anything specific — pricing, competitors, compliance, risks."],
        "open_tabs": ["structural", "compliance"],
        "followups": ["What do they actually do?", "Who already does this?", "What kills companies like this?"],
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
            "Every term is defined in plain words at the bottom of Tab 9.",
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
        return {
            "answer": f"How {_subject(report)} actually reaches people — the concrete mechanics, not the 'they do digital marketing' filler:",
            "bullets": bullets or ["No marketing mechanics were visible in this run's evidence — decode with network for the full picture."],
            "open_tabs": ["deepdive"],
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
    """Definitions only, from the dna-tab vocabularies. The Founder-School
    lesson engine died in the pure-research cut — a definition is research-
    adjacent; a curriculum was not."""
    from .data.dna import BUSINESS_GLOSSARY, PSYCH_GLOSSARY
    low = q.lower()
    for source, gloss in (("business", BUSINESS_GLOSSARY), ("psychology", PSYCH_GLOSSARY)):
        for term, definition in gloss.items():
            for alias in term.replace("(", "").split(" / "):
                if re.search(rf"\b{re.escape(alias.lower())}\b", low):
                    return {"answer": f"{term}: {definition}",
                            "bullets": [f"Source: the {source} vocabulary in Tab 9 (Product DNA)."],
                            "open_tabs": ["dna"], "followups": ["What do they actually do?"]}
    return {
        "answer": "That term isn't in the decoded brief's vocabularies — ask me about a feature or pattern from this decode instead.",
        "bullets": [],
        "open_tabs": ["dna"],
        "followups": ["What do they actually do?"],
    }


_HANDLERS = {
    "hello": _advise_hello,
    "competitors": _advise_competitors,
    "mvp": _advise_mvp,
    "compliance": _advise_compliance,
    "pricing": _advise_pricing,
    "risk": _advise_risk,
    "redteam": _advise_redteam,
    "dna": _advise_dna,
    "teach": _advise_teach,
    "markets": _advise_markets,
    "deepdive": _advise_deepdive,
    "next": _advise_next,
}
