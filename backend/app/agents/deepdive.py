"""Tab 17 — Company Deep-Dive: what they do, every feature, the reality, the marketing.

Four layers, all in plain words, all evidence-backed:
  WHAT THEY DO      - the problem in real user words, the solution, the founding trigger
  FEATURE INVENTORY - real product features (mined from the company's own site +
                      the release/evidence trail), each with the issue people had
                      before it, the trigger that produced it, its impact, and the
                      psychological/evolutionary basis. Release/acquisition events
                      are separated into product_milestones so the inventory stays
                      a product surface, not a news feed.
  REALITY CHECK     - the things a builder will actually come across (observations,
                      not advice), personalized with the dossier's own numbers
  MARKETING         - the concrete mechanics detected in the evidence, scored by
                      how many of the mechanic's own signals each snippet hits
"""
from __future__ import annotations

import asyncio
import re

from ..data import deepdive as KB
from ..data.dna import PATTERNS as DNA_PATTERNS
from ..models import Evidence
from ..scrapers.client import Fetcher, safe_public_http_url
from .base import Agent

# principles with a strong evolutionary basis - the "evolution" lens lines
EVOLUTION = {
    "Social proof": "Evolution made herd-following cheap and safe: when others chose something and survived, copying them cost nothing. That instinct predates language.",
    "Loss aversion": "Evolution weighted losses heavily because missing a threat once could end the bloodline. Streaks, expiring offers and paywalls all pull this ancient lever.",
    "Reciprocity": "Sharing food and help created obligation loops in every human society; free value triggers the same ancient ledger.",
    "Authority bias": "Hierarchies decided survival for millennia; badges, titles and institutions borrow that wiring.",
    "Default bias": "Energy conservation is evolutionary: the option that needs no action wins unless the stakes are visible.",
}

# news-shaped sentences are milestones, not features
_EVENT_WORDS = ("released", "launch", "acquired", "raised", "introduced", "announced",
                "unveiled", "shipped", "founded", "merged", "version ", "series ")

# site nav/legal headings are never features
_NAV_JUNK = re.compile(
    r"^(log ?in|sign ?up|sign ?in|register|pricing$|careers?|jobs?|contact|about( us)?|blog|docs?|"
    r"documentation|download|faq|support|help|privacy|terms|cookies?|press|security|status|"
    r"newsletter|get started|start (for )?free|book a demo|request a demo|learn more|read more|"
    r"see (all|more)|customers?|community$|company|resources?|changelog|twitter|linkedin|youtube|"
    r"all rights reserved|©|menu|search|home$)",
    re.I,
)

_SITE_PATHS = ("", "/features", "/product", "/platform", "/pricing")


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

        raw_rows = data("features").get("features") or []
        dna = data("dna")
        timeline = data("timeline")
        prem = data("premortem")
        comp = data("compliance")
        dist = data("distribution")
        pricing = data("pricing")
        fin = (data("financial").get("computed") or {})

        # ---------- mine the company's own site for the real product surface ----------
        f = Fetcher(ev)
        site_feats, site_meta = await self._site_intel(f, ev)

        # ---------- 1. what they do ----------
        user_words = self._user_words(sections, ev)
        what_they_do = {
            "the_problem": (
                f"People dealing with {ev.sector} work are living with friction the current tools never fully "
                "removed - the evidence shows it in their own words below. The problem is rarely that no tool "
                "exists; it's that the existing ones stop halfway."
            ) if is_idea else (
                f"{ev.subject} exists because a specific job in {ev.sector} was being done badly by the default "
                "options. The public record shows where the old way broke:"
            ),
            "the_problem_in_user_words": user_words,
            "the_solution": self._solution_summary(site_feats, raw_rows, site_meta, ev),
            "the_trigger": self._origin_story(ev, timeline),
            "founder_logic": (
                "Founders don't start from 'a great idea'; they start from a repeated annoyance they "
                "experienced or witnessed closely enough to believe they can remove it. Everything after "
                "the first version is the market editing that belief."
            ),
        }

        # ---------- 2. feature inventory (real product surface) + milestones ----------
        inventory, milestones = self._inventory(site_feats, raw_rows, dna, timeline)

        # ---------- 3. reality check ----------
        reality = self._reality_check(comp, prem, fin, dist, pricing, sections, ev)

        # ---------- 4. marketing mechanics ----------
        marketing = self._marketing(ev, dna, dist, pricing, inventory, milestones)

        return {
            "subject": ev.subject,
            "mode": ev.req.mode.value,
            "what_they_do": what_they_do,
            "feature_inventory": inventory,
            "product_milestones": milestones,
            "reality_check": reality,
            "marketing": marketing,
            "note": ("Plain words throughout: every term is defined in Founder School (Tab 15) and Product "
                     "DNA (Tab 14). The reality check observes - it doesn't tell you what to do."),
        }

    # ---------------------------------------------------------------- helpers

    def _looks_like_event(self, name: str) -> bool:
        low = name.lower()
        return any(w in low for w in _EVENT_WORDS)

    def _trim_words(self, name: str, limit: int = 70) -> str:
        name = " ".join(name.split())
        if len(name) <= limit:
            return name
        cut = name[:limit]
        return cut[:cut.rfind(" ")] if " " in cut else cut

    # ------------------------------------------------------------- site mining

    _EXCLUDED_DOMAINS = {
        "en.wikipedia.org", "linkedin.com", "crunchbase.com", "youtube.com",
        "facebook.com", "x.com", "twitter.com", "news.google.com", "medium.com",
        "reddit.com", "news.ycombinator.com", "g2.com", "trustpilot.com",
        "capterra.com", "producthunt.com", "github.com", "forbes.com",
        "bloomberg.com", "techcrunch.com", "theverge.com", "wikipedia.org",
    }

    def _domain_scan(self, results: list[dict], tokens: list[str]) -> str:
        """First credible domain containing a subject token."""
        from ..text import domain_of
        seen: set[str] = set()
        for r in results:
            d = (domain_of(r.get("url") or "") or "").strip()
            if not d or d in seen or d in self._EXCLUDED_DOMAINS:
                continue
            seen.add(d)
            if not re.fullmatch(r"[a-z0-9-]+(\.[a-z0-9-]+)+", d):
                continue
            if not safe_public_http_url(f"https://{d}"):
                continue
            if any(t in d for t in tokens):
                return d
        return ""

    async def _resolve_domain(self, f: Fetcher, ev: Evidence) -> str:
        """The company's own domain: recon's hint, evidence URLs, or one targeted search."""
        tokens = [t for t in dict.fromkeys(re.findall(r"[a-z0-9]{4,}", ev.subject.lower()))]
        if not tokens:
            return ""
        hint = (getattr(ev, "wiki_domain_hint", "") or "").strip()
        if hint:
            return hint
        domain = self._domain_scan(ev.search, tokens)
        if domain or f.offline:
            return domain
        try:
            from ..scrapers.search import ddg_search
            batch = await ddg_search(f, f"{ev.subject} official website", 8)
            if isinstance(batch, list):
                return self._domain_scan(batch, tokens)
        except Exception:
            pass
        return ""

    async def _site_intel(self, f: Fetcher, ev: Evidence) -> tuple[list[dict], str]:
        """Fetch the company's own marketing pages and extract feature headings."""
        domain = await self._resolve_domain(f, ev)
        if not domain or f.offline:
            return [], ""
        base = f"https://{domain}"
        if not safe_public_http_url(base):
            return [], ""
        pages = await asyncio.gather(*[f.try_text(f"{base}{path}") for path in _SITE_PATHS])
        feats: list[dict] = []
        meta = ""
        for r in pages:
            if not isinstance(r, str) or len(r) < 200:
                continue
            page_feats, page_meta = self._parse_site_page(r, f"{base}")
            meta = meta or page_meta
            feats.extend(page_feats)
        return feats, meta

    def _parse_site_page(self, html: str, page_url: str) -> tuple[list[dict], str]:
        from ..scrapers.client import soup
        from ..text import clean
        try:
            s = soup(html)
        except Exception:
            return [], ""
        for tag in s(["script", "style", "noscript", "svg", "footer", "nav", "header"]):
            tag.decompose()
        meta = ""
        mt = s.find("meta", attrs={"name": "description"}) or s.find("meta", attrs={"property": "og:description"})
        if mt and mt.get("content"):
            meta = clean(str(mt.get("content")))[:300]
        out: list[dict] = []
        for h in s.find_all(["h1", "h2", "h3"]):
            t = clean(h.get_text(" "))
            t = t.rstrip(" →←•·|-–—").strip()
            if not (3 <= len(t) <= 90) or self._looks_like_event(t) or _NAV_JUNK.search(t):
                continue
            out.append({"feature": t[:140], "detail": "", "class": "on-site",
                        "date": "", "source": "company-site", "url": page_url})
        return out, meta

    # ------------------------------------------------------------- what they do

    # product-context words: a complaint about "the export breaking" is about the
    # product even when it never names it; news headlines ("canceled trips") fail this
    _PRODUCT_CONTEXT = re.compile(
        r"\b(app|tool|product|software|platform|feature|pricing|plan|subscription|upgrade|"
        r"onboarding|support|refund|billing|export|import|integrations?|workspace|dashboard|"
        r"account|bugs?|crash(ed|es|ing)?|log ?in|workflow|free tier|paid|trial|teams?\b|"
        r"users?|ui|ux|notes?|docs?|pages?)\b", re.I)

    def _user_words(self, sections: dict, ev: Evidence) -> list[dict]:
        """Real complaint voices, quoted - the problem in the users' own words."""
        out: list[dict] = []
        seen: set[str] = set()
        tokens = re.findall(r"[a-z0-9]{4,}", ev.subject.lower())

        def _clean_quote(text: str) -> str:
            # "X X Source" echo from title+snippet duplication (punctuation-insensitive)
            words = text.split()
            def norm(w: str) -> str:
                return w.lower().strip(".,!?;:()\"'")
            for size in range(len(words) // 2, 2, -1):
                if [norm(w) for w in words[:size]] == [norm(w) for w in words[size:size * 2]]:
                    text = " ".join(words[size:])
                    break
            # rating-card boilerplate is not a complaint voice
            if re.search(r"\bis rated\b|\b\d(?:\.\d)?\s*/\s*5\b|\bout of 5\b", text, re.I):
                return ""
            return text.strip()

        def add(v: dict, source_label: str) -> None:
            text = _clean_quote(" ".join(str(v.get("text") or v.get("quote") or "").split()))
            if not (25 <= len(text) <= 240):
                return
            low = text.lower()
            # must be ABOUT the subject's product: names it, or reads like a product complaint
            if not any(t in low for t in tokens) and not self._PRODUCT_CONTEXT.search(text):
                return
            key = text[:60].lower()
            if key in seen:
                return
            seen.add(key)
            out.append({"quote": text, "source": str(v.get("source") or source_label), "url": v.get("url") or None})

        fr = ((sections.get("friction") or {}).get("data") or {})
        for v in (fr.get("representative_voices") or [])[:14]:
            add(v, "public review")
        st = ((sections.get("structural") or {}).get("data") or {})
        for v in (st.get("pain_points") or [])[:10]:
            add(v, "public post")
        return out[:3]

    def _origin_story(self, ev: Evidence, timeline: dict) -> str:
        """The founding sentence from the evidence, or the first timeline event."""
        if ev.wiki:
            summ = str(ev.wiki.get("summary") or "")
            for sent in re.split(r"(?<=[.!?])\s+", summ):
                if len(sent) > 40 and re.search(r"\b(founded|founding|created|started|began|developed by)\b", sent, re.I):
                    return sent[:340]
            if summ:
                return summ[:400]
        events = timeline.get("events") or timeline.get("gates") or []
        if events:
            first = events[0]
            return str(first.get("what") or first.get("event") or "")[:300]
        return "Origin not in the evidence corpus - decode with network for the founding story."

    def _solution_summary(self, site_feats: list[dict], raw_rows: list[dict], site_meta: str, ev: Evidence) -> str:
        names: list[str] = []
        seen: set[str] = set()
        for r in list(site_feats) + list(raw_rows):
            if self._looks_like_event(r.get("feature") or ""):
                continue
            name = self._trim_words(r.get("feature") or "")
            if name and name.lower() not in seen:
                seen.add(name.lower())
                names.append(name)
        products = names[:4]
        events = [self._trim_words(r.get("feature") or "", 80) for r in raw_rows
                  if self._looks_like_event(r.get("feature") or "")]
        meta_line = f' Their own site puts it in one line: "{site_meta}"' if site_meta else ""
        if len(products) >= 2:
            return ("The solution is a stack: " + "; ".join(products) +
                    f". Each one removes a specific piece of the manual work in {ev.sector}.{meta_line}")
        if events:
            return ("The public record shows the build sequence: " + " → ".join(events[:3]) +
                    f". The product surface itself is broken down feature by feature below.{meta_line}")
        if products:
            return (f"The known surface so far: {products[0]}. The full product spread wasn't in "
                    f"this run's evidence - decode again with network for the complete picture.{meta_line}")
        if site_meta:
            return f"Their own site describes it as: \"{site_meta}\""
        return (f"The solution shape for a {ev.sector} idea: one narrow job done dramatically better, "
                "then the feature ladder built around that wedge.")

    # ---------------------------------------------------------------- inventory

    def _inventory(self, site_feats: list[dict], raw_rows: list[dict], dna: dict, timeline: dict) -> tuple[list[dict], list[dict]]:
        product_rows = [r for r in raw_rows if not self._looks_like_event(r.get("feature") or "")]
        milestone_rows = [r for r in raw_rows if self._looks_like_event(r.get("feature") or "")]

        milestones = [{"what": (r.get("feature") or "")[:160], "when": str(r.get("date") or ""),
                       "url": r.get("url") or None} for r in milestone_rows]
        dated = [m for m in milestones if m["when"]]
        undated = [m for m in milestones if not m["when"]]
        milestones = (dated + undated)[:6]

        inventory: list[dict] = []
        seen: set[str] = set()
        for f in list(site_feats) + list(product_rows):
            name = " ".join((f.get("feature") or "").split())[:140]
            key = name.lower()[:60]
            if not name or key in seen:
                continue
            seen.add(key)
            patterns = self._patterns_for(name + " " + str(f.get("detail", "")))
            principle_names = [n for pat in patterns for n, _ in pat["psychology"]]
            issue = next((KB.USER_ISSUES.get(p["name"]) for p in patterns if p["name"] in KB.USER_ISSUES), None)
            kind = "on-site" if f.get("source") == "company-site" else (f.get("class") or ("minor" if len(name.split()) > 6 else "major"))
            inventory.append({
                "feature": name,
                "kind": kind,
                "what_it_does": self._trim_words(f.get("detail") or name, 200),
                "the_issue_before": issue or (
                    f"Before this existed, users handled it manually or tolerated the friction - the "
                    f"workaround itself is the proof the need was real."
                ),
                "the_trigger": self._trigger_for(f, timeline),
                "the_impact": self._impact_for(f, dna),
                "psych_basis": principle_names[:3],
                "evolution": _evolution_for(principle_names[:3]),
            })
            if len(inventory) >= 16:
                break
        return inventory, milestones

    def _trigger_for(self, f: dict, timeline: dict) -> str:
        if f.get("source") == "company-site":
            return "Live on their own site today - it's a current selling surface, not a historical add-on."
        date = f.get("date") or ""
        name_l = " ".join((f.get("feature") or "").lower().split())[:60]
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

    # ------------------------------------------------------------- reality check

    def _reality_check(self, comp: dict, prem: dict, fin: dict, dist: dict,
                       pricing: dict, sections: dict, ev: Evidence) -> dict:
        checks = [dict(rc) for rc in KB.REALITY_CHECKS]

        def amend(area_key: str, extra: str) -> None:
            nonlocal checks
            checks = [dict(c) if c["area"] != area_key else {**c, "what": f"{c['what']} {extra}"}
                      for c in checks]

        n_voices = len(((sections.get("friction") or {}).get("data") or {}).get("representative_voices") or []) \
            + len(((sections.get("structural") or {}).get("data") or {}).get("pain_points") or [])
        if n_voices:
            amend("Support is the hidden second product",
                  f"This space already has {n_voices} public complaint voices in the evidence - every one is a support conversation waiting to happen.")

        critical = comp.get("critical_count")
        if critical:
            amend("Compliance arrives before you feel ready",
                  f"For this idea specifically: {critical} launch-blocking obligations are already identified in Tab 3.")

        pivots = (((sections.get("timeline") or {}).get("data") or {}).get("pivots") or [])
        if pivots:
            amend("The first version will embarrass you",
                  f"Their own timeline shows {len(pivots)} pivot(s) - the sure roadmap gets rewritten in every market.")

        alts = (((sections.get("features") or {}).get("data") or {}).get("alternatives") or {}).get("candidates") or []
        if alts:
            amend("Competition responds",
                  f"The alternatives scan already names: {', '.join(str(a) for a in alts[:5])}.")

        if fin.get("breakeven_customers"):
            amend("Cash cycles lag effort",
                  f"For this team: {fin['breakeven_customers']:,} paying customers before the burn is covered, "
                  f"at a {fin.get('burn_month', 0):,}/month burn - that's the number the cash cycle has to reach.")

        modes = prem.get("common_failure_modes") or []
        if modes:
            amend("Growth is not a straight line",
                  "The failure records matched to this domain: " +
                  "; ".join(str(m.get("mode", "")) for m in modes[:3]) + ".")

        tiers = pricing.get("tiers") or []
        if len(tiers) >= 3:
            amend("Competition responds",
                  f"Their pricing page runs {len(tiers)} tiers - you will be compared line by line against a page that A/B tests every word.")
        return {"items": checks[:8]}

    # ----------------------------------------------------------------- marketing

    def _marketing_corpus(self, ev: Evidence) -> list[tuple[str, str]]:
        """(text, url) pairs from every evidence source that carries a snippet."""
        items: list[tuple[str, str]] = []
        for r in ev.search:
            t = " ".join((str(r.get("title") or "") + ". " + str(r.get("snippet") or "")).split())
            if t:
                items.append((t, str(r.get("url") or "")))
        for r in ev.reviews:
            t = " ".join((str(r.get("title") or "") + ". " + str(r.get("snippet") or "")).split())
            if t:
                items.append((t, str(r.get("url") or "")))
        for r in ev.hn_stories:
            t = " ".join(str(r.get("title") or "").split())
            if t:
                items.append((t, str(r.get("url") or "")))
        for r in ev.reddit:
            t = " ".join((str(r.get("title") or "") + " " + str(r.get("selftext") or "")).split())
            if t:
                items.append((t, str(r.get("url") or "")))
        return items

    def _marketing(self, ev: Evidence, dna: dict, dist: dict, pricing: dict,
                   inventory: list[dict], milestones: list[dict]) -> dict:
        corpus = self._marketing_corpus(ev)
        detected: list[dict] = []
        for mech in KB.MARKETING_MECHANICS:
            scored: list[tuple[int, str, str]] = []
            for text, url in corpus:
                low = text.lower()
                hits = [kw for kw in mech["kw"] if kw in low]
                if hits:
                    scored.append((len(hits), text, url))
            dna_signal = any(p["name"] == mech["name"] for p in (dna.get("product_philosophy") or {}).get("top_patterns") or [])
            if not scored and not dna_signal:
                continue
            scored.sort(key=lambda x: -x[0])
            _, best_text, best_url = scored[0] if scored else (0, "", "")
            signals = [kw for kw in mech["kw"] if kw in best_text.lower()][:4] if best_text else []
            detected.append({
                "mechanic": mech["name"],
                "signals": signals,
                "dna_confirmed": dna_signal,
                "how_they_used_it": (best_text[:240] if best_text else
                                     "Not directly evidenced in this run - the mechanic is standard for this category."),
                "evidence_url": best_url or None,
                "what_they_promote": mech["promotes"],
                "psych": mech["psych"],
            })

        # the hook: a free/trial tier on the pricing page, else the dna freemium feature
        hook = ""
        for t in pricing.get("tiers") or []:
            tname = str(t.get("name") or "")
            if "free" in tname.lower() or "trial" in tname.lower():
                hook = f"the {tname} tier - the try-before-you-buy surface the whole funnel hangs on"
                break
        if not hook:
            hook = next((f.get("feature", "")[:80] for f in dna.get("features") or []
                         if any(p["name"] == "Freemium / free tier" for p in f.get("patterns", []))), "")
        if not hook:
            hook = "the core workflow (no freemium hook detected)"

        # what they're pushing right now: the newest dated surfaces in the record
        dated: list[tuple[str, str]] = []
        for m in milestones:
            if m.get("when"):
                dated.append((str(m["when"]), str(m["what"])))
        current_push = [n for _, n in sorted(dated, key=lambda x: x[0], reverse=True)[:3] if n]

        return {
            "mechanics": detected[:8],
            "the_hook": hook,
            "current_push": current_push,
            "channel_ranking": [c.get("name", "") for c in (dist.get("channels") or [])[:3]],
            "note": ("Detected from the evidence + cross-referenced with the DNA and distribution tabs. "
                     "Absence of a mechanic in the evidence means 'not visible', not 'not used'."),
        }

    def _patterns_for(self, text: str) -> list[dict]:
        low = text.lower()
        return [p for p in DNA_PATTERNS if any(kw in low for kw in p["kw"])]

    def summarize(self, ev: Evidence, data: dict) -> str:
        n = len(data.get("feature_inventory", []))
        ms = len(data.get("product_milestones", []))
        m = len((data.get("marketing") or {}).get("mechanics", []))
        r = len((data.get("reality_check") or {}).get("items", []))
        return (f"Deep-dive: what {ev.subject} does, {n} real features inventoried (issue, trigger, impact, "
                f"psychology each) + {ms} milestones kept separate, {r} reality checks, and {m} concrete "
                f"marketing mechanics detected.")
