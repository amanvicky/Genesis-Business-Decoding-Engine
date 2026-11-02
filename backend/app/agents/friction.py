"""Tab 7 — Market Friction & Consumer Psychology (unvarnished voice mining)."""
from __future__ import annotations

import re
from collections import Counter

from ..models import Evidence
from ..text import clean
from .base import Agent

COMPLAINT_PATTERNS = {
    "Pricing/value mismatch": [r"too expensive", r"price(hike| increase|d)?", r"overpriced", r"hidden (fee|charge)", r"raised (their )?price"],
    "Support quality": [r"support (is|was)", r"no (response|reply)", r"customer service", r"ticket", r"ignored"],
    "Reliability/outages": [r"down (again)?", r"outage", r"crash", r"bug", r"breaks", r"slow"],
    "Billing traps": [r"charged", r"refund", r"cancel(led|lation)?", r"auto.renew", r"double.?charg"],
    "Complexity/UX": [r"confus", r"complicated", r"unintuitive", r"learning curve", r"onboarding"],
    "Missing features": [r"wish (it|they)", r"lacks", r"missing", r"no (support for|way to)"],
    "Compliance/trust": [r"scam", r"trust", r"security", r"data (breach|privacy)", r"fine", r"fraud"],
}

TRIGGER_PATTERNS = {
    "Event-driven switch": [r"switch(ed)? (to|from)", r"migrat", r"left .* for", r"after .* we moved"],
    "Hiring scale-outgrew tools": [r"grow(ing|th)", r"scaled", r"headcount", r"team of \d+"],
    "Compliance deadline": [r"audit", r"tax season", r"filing deadline", r"compliance"],
    "Cost-cutting mandate": [r"budget cut", r"save money", r"cheaper alternative"],
}


class FrictionAgent(Agent):
    id = "friction"
    title = "Market Friction & Consumer Psychology"
    icon = "🔥"
    tab = 7

    async def build(self, ev: Evidence) -> dict:
        corpus: list[dict] = []
        for r in ev.reddit:
            corpus.append({"source": f"r/{r.get('subreddit', '?')}", "text": clean(r.get("title") + ". " + r.get("selftext", ""))[:300], "url": r.get("url", ""), "weight": 1 + (r.get("score", 0) > 20)})
        for r in ev.hn_comments:
            corpus.append({"source": "Hacker News", "text": clean(r.get("text", ""))[:300], "url": r.get("url", ""), "weight": 1})
        for r in ev.reviews:
            corpus.append({"source": {"trustpilot": "Trustpilot", "g2": "G2", "capterra": "Capterra", "complaints": "Web complaints", "churn": "Churn posts"}.get(r.get("kind", ""), "Web"), "text": clean(r.get("title", "") + ". " + r.get("snippet", ""))[:300], "url": r.get("url", ""), "weight": 1})

        complaints: list[dict] = []
        matched: Counter[str] = Counter()
        for c in corpus:
            low = c["text"].lower()
            for label, pats in COMPLAINT_PATTERNS.items():
                if any(re.search(p, low) for p in pats):
                    matched[label] += 1
                    complaints.append({**c, "cluster": label})
        triggers: list[dict] = []
        tmatched: Counter[str] = Counter()
        for c in corpus:
            low = c["text"].lower()
            for label, pats in TRIGGER_PATTERNS.items():
                if any(re.search(p, low) for p in pats):
                    tmatched[label] += 1
                    if tmatched[label] <= 3:
                        triggers.append({**c, "trigger": label})

        ranked = [{"cluster": k, "count": v, "share": f"{round(100 * v / max(1, sum(matched.values())))}%"} for k, v in matched.most_common()]
        return {
            "voice_count": len(corpus),
            "complaint_clusters": ranked,
            "representative_voices": complaints[:15],
            "demand_triggers": triggers[:9],
            "trigger_summary": [{"trigger": k, "count": v} for k, v in tmatched.most_common()],
            "caveat": "Public-forum skews negative (people post when broken, not when fine). Treat cluster ratios, not absolute counts, as signal.",
        }

    def summarize(self, ev: Evidence, data: dict) -> str:
        top = data["complaint_clusters"][0] if data["complaint_clusters"] else None
        n = data["voice_count"]
        trigger = data["trigger_summary"][0]["trigger"] if data["trigger_summary"] else "none captured"
        if not top:
            return f"{n} public voices mined — no complaint clusters surfaced at this evidence depth. Widen with more sources or interviews."
        return f"{n} public voices mined. Dominant friction: {top['cluster']} ({top['share']} of complaints) — top demand trigger: {trigger}."

    def llm_prompt(self, ev: Evidence, data: dict) -> str:
        return f"Subject: {ev.subject}. From these public voices, state the ONE complaint that, if fixed as a product feature, would convert competitors' churned users."
