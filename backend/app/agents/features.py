"""Tab 2 — Granular Feature Breakdown & MVP Sequencing (the Feature Decompiler)."""
from __future__ import annotations

import re
from datetime import datetime

from ..models import Evidence
from ..text import classify_feature, clean, keyphrases, sentences
from .base import Agent

DATE_RES = [
    re.compile(r"\b(20\d\d)[-/.](\d{1,2})[-/.](\d{1,2})\b"),
    re.compile(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(\d{1,2})?,?\s+(20\d\d)\b", re.I),
]

MVP_ORDER = ["auth", "dashboard", "core action", "notifications", "integrations", "billing", "admin", "analytics", "enterprise controls"]


class FeaturesAgent(Agent):
    id = "features"
    title = "Granular Feature Breakdown & MVP Sequencing"
    icon = "🧩"
    tab = 2

    async def build(self, ev: Evidence) -> dict:
        founded = (ev.wiki or {}).get("founded_year")
        features: list[dict] = []

        # Source 1: GitHub releases (highest fidelity when present)
        for rel in ev.releases:
            features.append({"date": rel.get("date") or "", "feature": rel.get("name", "")[:120], "detail": rel.get("body", "")[:200], "source": "github-releases", "url": rel.get("url", "")})

        # Source 2: Wikipedia history sentences that describe launches/products
        if ev.wiki:
            for s in sentences(ev.wiki.get("history", "") or ev.wiki.get("extract", "")):
                if re.search(r"\b(launch|released|introduced|added|rolled out|unveil|expand\w* into|acquired|pivot\w*)\b", s, re.I):
                    year = next((y for y in re.findall(r"\b(19[89]\d|20[0-3]\d)\b", s)), None)
                    features.append({"date": year or "", "feature": s[:160], "detail": "", "source": "wikipedia-history", "url": (ev.wiki or {}).get("url", "")})

        # Source 3: search snippets about releases/launches
        for r in ev.search:
            text = r.get("title", "") + " " + r.get("snippet", "")
            if re.search(r"\b(launch\w*|release[d-s]?|new feature|rolls? out|introduc\w+|now supports)\b", text, re.I):
                features.append({"date": "", "feature": text[:160], "detail": "", "source": "web-snippet", "url": r.get("url", "")})

        # Dedupe + classify
        seen: set[str] = set()
        cleaned: list[dict] = []
        for ft in features:
            key = ft["feature"].lower()[:60]
            if not key or key in seen:
                continue
            seen.add(key)
            years_old = None
            if founded and ft["date"]:
                try:
                    y = int(str(ft["date"])[:4])
                    years_old = y - founded
                except ValueError:
                    pass
            ft["class"] = classify_feature(ft["feature"], ft.get("detail", ""), years_old)
            cleaned.append(ft)

        cleaned.sort(key=lambda x: str(x.get("date") or "9999"))
        class_counts = {"day1": 0, "growth": 0, "enterprise": 0}
        for ft in cleaned:
            class_counts[ft["class"]] = class_counts.get(ft["class"], 0) + 1

        # True USP: distinctive repeated phrases across the corpus
        pool = ev.snippet_pool()
        phrases = keyphrases(pool, 10)
        usp_candidates = [{"phrase": p, "mentions": c} for p, c in phrases]

        # MVP sequencing for idea mode (or when the target's early history is thin)
        sequencing = self._sequence(cleaned)

        # v2: strict binary roadmap — BUILD / LATER / DO-NOT-BUILD
        roadmap = self._binary_roadmap(ev, cleaned)

        return {
            "founded_year": founded,
            "feature_count": len(cleaned),
            "class_counts": class_counts,
            "features": cleaned[:60],
            "binary_roadmap": roadmap,
            "usp_candidates": usp_candidates,
            "true_usp": (usp_candidates[0]["phrase"].title() if usp_candidates else "Insufficient corpus — the target's positioning language is not repeating in public sources."),
            "mvp_sequence": sequencing,
            "note": "day1 = build this first to replicate the wedge; growth = post-PMF; enterprise = revenue-tier gating, not MVP scope.",
        }

    _IDEA_BLOAT = [
        ("SSO / SAML / SCIM", "after 3 enterprise procurement requests in writing"),
        ("Audit logs", "after your first regulated-industry pipeline exists"),
        ("Admin console / RBAC", "after 10-seat accounts actually appear"),
        ("Mobile apps", "after web week-4 retention > 40%"),
        ("Integrations marketplace", "after 10 unprompted integration asks"),
        ("White-label / multi-tenant theming", "after 2 signed reseller deals"),
    ]

    def _binary_roadmap(self, ev: Evidence, features: list[dict]) -> dict:
        build_now = [
            {"feature": f["feature"][:140], "why": "Day-1 wedge class — the target shipped this when it was tiny", "source": f.get("source", "")}
            for f in features
            if f.get("class") == "day1"
        ][:10]
        build_later = [
            {"feature": f["feature"][:140], "why": "post-PMF growth surface — sequence after retention proof, not before", "source": f.get("source", "")}
            for f in features
            if f.get("class") == "growth"
        ][:10]
        never = [
            {"feature": f["feature"][:140], "why": "enterprise bloat: procurement theater, not the wedge", "gate": "revisit only after 3 written enterprise commitments"}
            for f in features
            if f.get("class") == "enterprise"
        ][:10]

        if not build_now:
            # idea mode: the canonical zero-to-one build list
            build_now = [{"feature": s["build"], "why": "canonical MVP step", "source": "genesis-canonical"} for s in self._sequence([])][:8]
        if not never:
            never = [
                {"feature": name, "why": "enterprise bloat: zero wedge value until paid demand exists", "gate": gate}
                for name, gate in self._IDEA_BLOAT
            ]
        return {"build_now": build_now, "build_later": build_later, "never_for_mvp": never}

    def _sequence(self, features: list[dict]) -> list[dict]:
        day1 = [f for f in features if f.get("class") == "day1"][:12]
        seq: list[dict] = []
        if day1:
            ordered: list[str] = []
            for kw in MVP_ORDER:
                for f in day1:
                    if kw.split()[0] in f["feature"].lower() and f["feature"] not in ordered:
                        ordered.append(f["feature"])
            rest = [f["feature"] for f in day1 if f["feature"] not in ordered]
            final = (ordered + rest)[:12]
            for i, name in enumerate(final, 1):
                seq.append({"order": i, "build": name})
        else:
            # idea mode fallback: canonical zero-to-one sequence
            canonical = [
                ("1", "Auth + minimal identity (email OTP — no password flows, no OAuth sprawl)"),
                ("2", "The single core action that delivers the promised value (ONE screen)"),
                ("3", "Manual back-office behind the scenes (concierge MVP — humans do what you'll automate)"),
                ("4", "Notifications that create the habit loop (email/WhatsApp before in-app)"),
                ("5", "Billing wired to the compliance-approved gateway (Razorpay IN / Stripe US)"),
                ("6", "Analytics on the ONE activation metric (do users complete the core action twice?)"),
            ]
            seq = [{"order": o, "build": b} for o, b in canonical]
        return seq

    def summarize(self, ev: Evidence, data: dict) -> str:
        cc = data["class_counts"]
        return f"{data['feature_count']} features decompiled — {cc.get('day1', 0)} Day-1 class, {cc.get('growth', 0)} growth-era, {cc.get('enterprise', 0)} enterprise-tier. True USP candidate: '{data['true_usp']}'."

    def llm_prompt(self, ev: Evidence, data: dict) -> str:
        return (
            f"Subject: {ev.subject}. From the feature/changelog evidence, name the ONE feature that made users switch "
            "(the wedge), the one feature that is pure enterprise-theater, and what the founder should cut from an MVP today."
        )
