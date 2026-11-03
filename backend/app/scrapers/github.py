"""GitHub public API (unauthenticated): repos + release changelogs of the target."""
from __future__ import annotations

import re
from urllib.parse import quote_plus

from .client import Fetcher
from ..text import clean


def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


async def find_repo(fetcher: Fetcher, subject: str) -> dict | None:
    data = await fetcher.try_json(
        f"https://api.github.com/search/repositories?q={quote_plus(subject)}&per_page=5&sort=stars",
        kind="github",
    )
    items = (data or {}).get("items", [])
    if not items:
        return None
    # The subject must match the repo name at a word boundary AND be mentioned
    # in the repo description (or the name must be exactly the token). This
    # rejects "adPEAS" (Active Directory toolkit) and "adp-delightful-details"
    # (an Android animations sample) that star-rank above real matches.
    token = _norm((subject.split() or [""])[0])
    prefix = re.compile(rf"^{re.escape(token)}\b")
    for item in items:
        name = (item.get("name") or "").lower()
        description = _norm(item.get("description") or "")
        if prefix.match(name) and (token in description or _norm(name) == token):
            return item
    return None


async def releases(fetcher: Fetcher, full_name: str, limit: int = 40) -> list[dict]:
    # full_name comes from the GitHub API response — validate its shape before
    # interpolating into the URL (host is pinned; this blocks path/query smuggling)
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", full_name or ""):
        return []
    data = await fetcher.try_json(
        f"https://api.github.com/repos/{full_name}/releases?per_page={limit}",
        kind="github",
    )
    out = []
    for rel in data or []:
        name = clean(rel.get("name") or rel.get("tag_name") or "")
        if not name:
            continue
        out.append(
            {
                "name": name,
                "body": clean(rel.get("body") or "")[:800],
                "date": (rel.get("published_at") or "")[:10],
                "url": rel.get("html_url", ""),
            }
        )
    return out
