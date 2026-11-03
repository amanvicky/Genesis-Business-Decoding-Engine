"""Recon agent: gathers the raw evidence bundle every analysis agent shares.

Runs all free scrapers with soft failure — a blocked source degrades the
report, never kills it. Every step streams a console event.
"""
from __future__ import annotations

import asyncio
import re

from ..models import Evidence
from ..scrapers.client import Fetcher, safe_public_http_url
from ..scrapers import github, hn, reddit, reviews, search, wayback, wikipedia
from ..text import clean, detect_sector, domain_of
from .base import Agent, Emit


class ReconAgent(Agent):
    id = "recon"
    title = "Recon: multi-source evidence gathering"
    icon = "🛰"

    async def run_recon(self, ev: Evidence, emit: Emit) -> Evidence:
        f = Fetcher(ev)
        q = ev.req.query
        mode = ev.req.mode.value
        geo = ev.req.geography.value

        await emit({"type": "log", "level": "agent", "agent": self.id, "msg": f"target: '{q}' (mode={mode}, geo={geo}, sector={ev.sector})"})

        if f.offline:
            await emit({"type": "log", "level": "warn", "agent": self.id, "msg": "GENESIS_OFFLINE=1 — using built-in knowledge bases only (no network)"})

        # 1. Surface web
        await emit({"type": "log", "level": "info", "agent": self.id, "msg": "scanning surface web (search cascade)…"})
        if mode == "company":
            # Qualify with 'company': bare acronyms (ADP, BAT…) drag in unrelated domains.
            base_queries = [f"{q} company", f"{q} business model revenue how does", f"{q} pricing tiers plans"]
        else:
            base_queries = [q, f"{q} startup problem market", f"{q} how much do companies pay"]
        batches = await asyncio.gather(*[search.ddg_search(f, bq, 10) for bq in base_queries], return_exceptions=True)
        seen: set[str] = set()
        for batch in batches:
            if isinstance(batch, Exception):
                await emit({"type": "log", "level": "warn", "agent": self.id, "msg": "surface search partially blocked (engine rate limit) — continuing"})
                continue
            for r in batch:
                if r["url"] not in seen:
                    seen.add(r["url"])
                    ev.search.append(r)

        # 1b. Direct news coverage for company subjects — keyless RSS works even
        # where HTML search engines block automated traffic.
        if mode == "company":
            news = await search.news_search(f, q, 10)
            fresh = 0
            for r in news:
                if r["url"] not in seen:
                    seen.add(r["url"])
                    ev.search.append(r)
                    fresh += 1
            if fresh:
                await emit({"type": "log", "level": "success", "agent": self.id, "msg": f"news coverage: {fresh} recent articles (Google/Bing News RSS)"})

        # Infer the company's website domain from search results (company mode)
        company_domain = ""
        if mode == "company":
            for r in ev.search:
                d = domain_of(r["url"])
                # Strict domain format + SSRF gate: this value is fetched from
                # later, and search results are attacker-rankable — a netloc
                # like "user@10.0.0.5:8080" must never pass.
                if (d and safe_public_http_url(f"https://{d}")
                        and re.fullmatch(r"[a-z0-9-]+(\.[a-z0-9-]+)+", d)
                        and d not in ("en.wikipedia.org", "linkedin.com", "crunchbase.com", "youtube.com", "facebook.com", "x.com", "twitter.com")):
                    head = (q.lower().split() or [""])[0]
                    if head in d or d.split(".")[0] == head.replace(" ", ""):
                        company_domain = d
                        break
        ev.wiki_domain_hint = company_domain  # type: ignore[attr-defined]
        await emit({"type": "log", "level": "success", "agent": self.id, "msg": f"surface web: {len(ev.search)} unique results"})

        # 2. Wikipedia genesis data
        if mode == "company":
            await emit({"type": "log", "level": "info", "agent": self.id, "msg": "decoding genesis via Wikipedia…"})
            ev.wiki = await wikipedia.company_brief(f, q)
            if ev.wiki:
                fy = ev.wiki.get("founded_year")
                await emit({"type": "log", "level": "success", "agent": self.id, "msg": f"Wikipedia: '{ev.wiki['title']}'" + (f" — founded {fy}" if fy else "")})
            else:
                await emit({"type": "log", "level": "warn", "agent": self.id, "msg": "no Wikipedia entry found — timeline will use search evidence"})

        # 3. Source triangulation: anchor results to a verified subject identity
        #    (kills acronym collisions like adPEAS-vs-ADP before analysis sees them)
        from ..engines.triangulation import triangulate

        await triangulate(ev, emit)

        # 4. HN + Reddit sentiment (parallel)
        await emit({"type": "log", "level": "info", "agent": self.id, "msg": "mining developer & consumer sentiment (HN Algolia, Reddit)…"})
        hn_s, hn_c, rd = await asyncio.gather(
            hn.hn_stories(f, q, 20),
            hn.hn_comments(f, f"{q} (shut down OR hate OR switch) ", 25),
            reddit.reddit_search(f, q, 30),
            return_exceptions=True,
        )
        if not isinstance(hn_s, Exception):
            ev.hn_stories = hn_s
        if not isinstance(hn_c, Exception):
            ev.hn_comments = hn_c
        if not isinstance(rd, Exception):
            ev.reddit = rd
        else:
            await emit({"type": "log", "level": "warn", "agent": self.id, "msg": "Reddit JSON rate-limited — friction analysis will lean on HN + review snippets"})
        await emit({"type": "log", "level": "success", "agent": self.id, "msg": f"sentiment pool: {len(ev.hn_stories)} stories, {len(ev.hn_comments)} threads, {len(ev.reddit)} reddit posts"})

        # 4. Changelogs / feature history
        if mode == "company":
            await emit({"type": "log", "level": "info", "agent": self.id, "msg": "decompiling feature history (GitHub releases + changelog pages)…"})
            repo = await github.find_repo(f, q)
            if repo:
                ev.releases = await github.releases(f, repo["full_name"], 40)
                await emit({"type": "log", "level": "success", "agent": self.id, "msg": f"GitHub: {repo['full_name']} ({repo.get('stargazers_count', 0)}★) — {len(ev.releases)} releases"})
            else:
                await emit({"type": "log", "level": "warn", "agent": self.id, "msg": "no GitHub repo matched — feature sequencing will use blog/docs search results"})
            if company_domain:
                for path in ("/changelog", "/release-notes", "/blog"):
                    txt = await f.try_text(f"https://{company_domain}{path}")
                    if txt and "<html" in txt.lower():
                        ev.search.append({"title": f"{company_domain}{path} (changelog)", "url": f"https://{company_domain}{path}", "snippet": clean(txt)[:400]})
                        break

        # 4b. Open financial filings (SEC EDGAR, free + keyless) for US-listed subjects
        if mode == "company" and geo in ("us", "global"):
            await emit({"type": "log", "level": "info", "agent": self.id, "msg": "cross-referencing SEC EDGAR filings (open financial layer)…"})
            from ..scrapers import filings

            profile = await filings.edgar_profile(
                f,
                q,
                (ev.wiki or {}).get("title"),
                expansion=" ".join(ev.identity.get("expansion") or []),
            )
            if profile and (profile.get("revenues") or profile.get("filings")):
                ev.financials = profile.get("revenues", [])
                ev.identity["edgar"] = {"cik": profile["cik"], "name": profile["name"], "ticker": profile.get("ticker")}
                rev = profile["revenues"][-1]["revenue_usd"] if profile.get("revenues") else None
                await emit({"type": "log", "level": "success", "agent": self.id, "msg": (
                    f"EDGAR: {profile['name']} (CIK {profile['cik']}, {profile.get('ticker')}) — "
                    + (f"latest annual revenue ${rev:,} " if rev else "")
                    + f"{len(profile['revenues'])} yrs revenue history, {len(profile['filings'])} recent 10-Ks"
                )})
            else:
                await emit({"type": "log", "level": "warn", "agent": self.id, "msg": "no EDGAR match — private/Indian companies have no free structured filings; financial layer skipped"})

        # 5. Review platforms
        await emit({"type": "log", "level": "info", "agent": self.id, "msg": "aggregating review-platform intelligence (search-snippet layer)…"})
        ev.reviews = await reviews.review_intel(f, q)
        await emit({"type": "log", "level": "success", "agent": self.id, "msg": f"review intel: {len(ev.reviews)} public snippets (Trustpilot/G2/Capterra layer)"})

        # 6. Wayback pricing history
        if mode == "company" and company_domain:
            await emit({"type": "log", "level": "info", "agent": self.id, "msg": f"reconstructing pricing history via Wayback Machine ({company_domain}/pricing)…"})
            ev.pricing_history = await wayback.pricing_history(f, company_domain)
            # "pricing" URLs come verbatim from search results — SSRF gate
            # before fetching: only public http(s) hosts are ever fetched.
            for path_url in [r["url"] for r in ev.search if "pricing" in r["url"] and safe_public_http_url(r["url"])][:1]:
                html = await f.try_text(path_url)
                if html:
                    from ..text import extract_tiers

                    ev.current_pricing = extract_tiers(clean(html))
            await emit({"type": "log", "level": "success", "agent": self.id, "msg": f"pricing archaeology: {len(ev.pricing_history)} historical snapshots"})

        await emit({"type": "log", "level": "success", "agent": self.id, "msg": f"recon complete — {len(ev.sources)} sources indexed"})
        return ev

    async def build(self, ev: Evidence):  # recon is driven directly by the pipeline
        return {}
