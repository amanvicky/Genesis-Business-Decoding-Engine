"""Tab 17 — Company Deep-Dive: what they do, every feature, the reality, the marketing.

Four layers, all in plain words:
  WHAT THEY DO      - the problem as users felt it, the solution, the founding trigger
  FEATURE INVENTORY - every discoverable feature (major and minor), each with the
                      issue people had before it, the trigger that produced it, its
                      impact, and the psychological/evolutionary basis
  REALITY CHECK     - the things a builder will actually come across (observations,
                      not advice)
  MARKETING         - the concrete mechanics detected in the evidence: how they
                      reached people and which feature they promote with it
"""
from __future__ import annotations

import re

from ..data import deepdive as KB
from ..data.dna import PATTERNS as DNA_PATTERNS
from ..models import Evidence
from .base import Agent

# principles with a strong evolutionary basis - the "evolution" lens lines
EVOLUTION = {
    "Social proof": "Evolution made herd-following cheap and safe: when others chose something and survived, copying them cost nothing. That instinct predates language.",
    "Loss aversion": "Evolution weighted losses heavily because missing a threat once could end the bloodline. Streaks, expiring offers and paywalls all pull this ancient lever.",
    "Reciprocity": "Sharing food and help created obligation loops in every human society; free value triggers the same ancient ledger.",
    "Authority bias": "Hierarchies decided survival for millennia; badges, titles and institutions borrow that wiring.",
    "Default bias": "Energy conservation is evolutionary: the option that needs no action wins unless the stakes are visible.",
}


def _evolution_for(principles: list[str]) -> str | None:
    for p in principles:
        if p in EVOLUTION:
            return EVOLUTION[p]
    return None


class DeepDiveAgent(Agent):
    id = "deepdive"
    title = "Company Deep-Dive — What, Why, Reality & Marketing"
    icon = "❖"
    tab = 17

    async def build(self, ev: Evidence) -> dict:
        is_idea = ev.req.mode.value == "idea"
        sections = getattr(self, "sections", {}) or {}

        def data(sid: str) -> dict:
            return ((sections.get(sid) or {}).get("data") or {})

        feats = data("features").get("features") or []
        dna = data("dna")
        timeline = data("timeline")
        prem = data("premortem")
        comp = data("compliance")
        dist = data("distribution")
        fin = (data("financial").get("computed") or {})
        pool = ev.snippet_pool(10000).lower()

        # ---------- 1. what they do ----------
        origin = ""
        history_events = timeline.get("events") or timeline.get("gates") or []
        if ev.wiki:
            origin = (ev.wiki.get("summary") or "")[:400]
        elif history_events:
            first = history_events[0]
            origin = str(first.get("what") or first.get("event") or "")[:300]

        what_they_do = {
            "the_problem": (
                f"People dealing with {ev.sector} work were living with friction that tools never fully removed - "
                "the dossier's pain and friction tabs hold the exact complaints. The problem is rarely that no "
                "tool exists; it's that the existing ones stop halfway."
            ) if is_idea else (
                f"{ev.subject} exists because a specific job in {ev.sector} was being done badly by the "
                "default options. The evidence trail (search, reviews, complaints) shows where the old way broke."
            ),
            "the_solution": self._solution_summary(feats, ev),
            "the_trigger": origin or "Origin not in the evidence corpus — decode with network for the founding story.",
            "founder_logic": (
                "Founders don't start from 'a great idea'; they start from a repeated annoyance they "
                "experienced or witnessed closely enough to believe they can remove it. Everything after "
                "the first version is the market editing that belief."
            ),
        }

        # ---------- 2. feature inventory (major + minor) ----------
        inventory: list[dict] = []
        seen: set[str] = set()
        for f in feats[:80]:
            name = (f.get("feature") or "")[:140]
            key = name.lower()[:60]
            if not name or key in seen:
                continue
            seen.add(key)
            patterns = self._patterns_for(name + " " + str(f.get("detail", "")))
            principle_names = [n for pat in patterns for n, _ in pat["psychology"]]
            issue = next((KB.USER_ISSUES.get(p["name"]) for p in patterns if p["name"] in KB.USER_ISSUES), None)
            inventory.append({
                "feature": name,
                "kind": f.get("class") or ("minor" if len(name.split()) > 6 else "major"),
                "what_it_does": (f.get("detail") or name)[:200],
                "the_issue_before": issue or (
                    f"Before this existed, users handled it manually or tolerated the friction - the "
                    f"workaround itself is the proof the need was real."
                ),
                "the_trigger": self._trigger_for(f, timeline, ev),
                "the_impact": self._impact_for(f, dna),
                "psych_basis": principle_names[:3],
                "evolution": _evolution_for(principle_names[:3]),
            })
            if len(inventory) >= 14:
                break

        # ---------- 3. reality check ----------
        reality = self._reality_check(comp, prem, fin, ev, pool)

        # ---------- 4. marketing mechanics ----------
        marketing = self._marketing(ev, dna, dist, pool)

        return {
            "subject": ev.subject,
            "mode": ev.req.mode.value,
            "what_they_do": what_they_do,
            "feature_inventory": inventory,
            "reality_check": reality,
            "marketing": marketing,
            "note": ("Plain words throughout: every term is defined in Founder School (Tab 15) and Product "
                     "DNA (Tab 14). The reality check observes - it doesn't tell you what to do."),
        }

    # ---------------------------------------------------------------- helpers

    _EVENT_WORDS = ("released", "launched", "acquired", "raised", "introduced",
                    "announced", "unveiled", "shipped", "founded", "merged")

    def _looks_like_event(self, name: str) -> bool:
        low = name.lower()
        return any(w in low for w in self._EVENT_WORDS)

    def _trim_words(self, name: str, limit: int = 70) -> str:
        name = " ".join(name.split())
        if len(name) <= limit:
            return name
        cut = name[:limit]
        return cut[:cut.rfind(" ")] if " " in cut else cut

    def _solution_summary(self, feats: list[dict], ev: Evidence) -> str:
        if feats:
            names: list[str] = []
            seen: set[str] = set()
            for f in sorted(feats, key=lambda f: len(f.get("feature") or "")):
                name = self._trim_words(f.get("feature") or "")
                if name and name.lower() not in seen:
                    seen.add(name.lower())
                    names.append(name)
            products = [n for n in names if not self._looks_like_event(n)]
            events = [n for n in names if self._looks_like_event(n)]
            if len(products) >= 2:
                return ("The solution is a stack: " + "; ".join(products[:4]) +
                        f". Each one removes a specific piece of the manual work in {ev.sector}.")
            if events:
                return ("The public record shows the build sequence: " + " → ".join(events[:3]) +
                        ". The product surface itself is broken down feature by feature below.")
            if products:
                return (f"The known surface so far: {products[0]}. The full product spread wasn't in "
                        f"this run's evidence - decode again with network for the complete picture.")
        return (f"The solution shape for a {ev.sector} idea: one narrow job done dramatically better, "
                "then the feature ladder built around that wedge.")

    def _trigger_for(self, f: dict, timeline: dict, ev: Evidence) -> str:
        date = f.get("date") or ""
        name_l = " ".join((f.get("feature") or "").lower().split())[:60]
        gates = timeline.get("gates") or []
        events = timeline.get("events") or []

        def circular(t: str) -> bool:
            # the "event" is just the same sentence the feature came from
            return bool(name_l) and name_l in " ".join(str(t).lower().split())

        if date and events:
            near = [e for e in events
                    if str(e.get("date") or e.get("year") or "").startswith(str(date)[:4])
                    and not circular(e.get("what") or e.get("event") or "")]
            if near:
                return f"Same period as: {str(near[0].get('what') or near[0].get('event') or '')[:140]}"
        if date:
            return f"Shipped around {date} - check what the company was scaling through at that moment."
        return "No dated trigger in the evidence - the need likely predates the record."

    def _impact_for(self, f: dict, dna_data: dict) -> str:
        name = (f.get("feature") or "").lower()
        for fb in dna_data.get("features") or []:
            if fb.get("feature", "").lower()[:40] in name or name[:40] in fb.get("feature", "").lower():
                outs = [o["text"] for pat in fb.get("patterns", []) for o in pat.get("played_out", [])]
                if outs:
                    text = outs[0]
                    # evidence titles sometimes arrive doubled ("X X Source") - drop the echo
                    words = text.split()
                    for size in range(len(words) // 2, 2, -1):
                        if words[:size] == words[size:size * 2]:
                            text = " ".join(words[size:])
                            break
                    return text[:200]
        return "Impact shows up in the numbers this feature protects (retention, conversion, expansion) - see Tabs 6 and 8."

    def _reality_check(self, comp: dict, prem: dict, fin: dict, ev: Evidence, pool: str) -> dict:
        checks = [dict(rc) for rc in KB.REALITY_CHECKS]
        critical = comp.get("critical_count")
        if critical:
            checks = [dict(c) if c["area"] != "Compliance arrives before you feel ready" else
                      {**c, "what": f"{c['what']} For this idea specifically: {critical} launch-blocking obligations are already identified in Tab 3."}
                      for c in checks]
        modes = prem.get("common_failure_modes") or []
        if modes:
            checks = [dict(c) if c["area"] != "Growth is not a straight line" else
                      {**c, "what": f"{c['what']} The failure records matched to this domain: " +
                       "; ".join(m.get("mode", "") for m in modes[:3]) + "."}
                      for c in checks]
        if fin.get("breakeven_customers"):
            checks = [dict(c) if c["area"] != "Cash cycles lag effort" else
                      {**c, "what": f"{c['what']} For this team: {fin['breakeven_customers']:,} paying customers "
                       f"before the burn is covered - that's the number the cash cycle has to reach."}
                      for c in checks]
        return {"items": checks[:8]}

    def _marketing(self, ev: Evidence, dna_data: dict, dist_data: dict, pool: str) -> dict:
        detected: list[dict] = []
        for mech in KB.MARKETING_MECHANICS:
            hits = [kw for kw in mech["kw"] if kw in pool]
            dna_signal = any(p["name"] == mech["name"] for p in (dna_data.get("product_philosophy") or {}).get("top_patterns") or [])
            channels = [c.get("name", "") for c in (dist_data.get("channels") or []) if c.get("name", "").lower() in mech["how"].lower()]
            evidence_bits = []
            if hits or dna_signal or channels:
                snippet = next((s for s in re.split(r"(?<=[.!?])\s+", pool) if any(kw in s for kw in mech["kw"])), "")
                evidence_bits = [snippet[:200]] if snippet else []
                detected.append({
                    "mechanic": mech["name"],
                    "signals": hits[:4],
                    "dna_confirmed": dna_signal,
                    "how_they_used_it": (evidence_bits[0] if evidence_bits else
                                         f"Not directly evidenced in this run - the mechanic is standard for this category."),
                    "what_they_promote": mech["promotes"],
                    "psych": mech["psych"],
                })
        hook = next((f.get("feature", "")[:80] for f in dna_data.get("features") or []
                     if any(p["name"] == "Freemium / free tier" for p in f.get("patterns", []))),
                    "the core workflow (no freemium hook detected)")
        return {
            "mechanics": detected[:8],
            "the_hook": hook,
            "channel_ranking": [c.get("name", "") for c in (dist_data.get("channels") or [])[:3]],
            "note": ("Detected from the evidence + cross-referenced with the DNA and distribution tabs. "
                     "Absence of a mechanic in the evidence means 'not visible', not 'not used'."),
        }

    def _patterns_for(self, text: str) -> list[dict]:
        low = text.lower()
        return [p for p in DNA_PATTERNS if any(kw in low for kw in p["kw"])]

    def summarize(self, ev: Evidence, data: dict) -> str:
        n = len(data.get("feature_inventory", []))
        m = len((data.get("marketing") or {}).get("mechanics", []))
        r = len((data.get("reality_check") or {}).get("items", []))
        return (f"Deep-dive: what {ev.subject} does, {n} features inventoried (issue, trigger, impact, "
                f"psychology for each), {r} reality checks, and {m} concrete marketing mechanics detected.")
