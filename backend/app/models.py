from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class Mode(str, Enum):
    company = "company"
    idea = "idea"


class Geography(str, Enum):
    india = "india"
    us = "us"
    global_ = "global"


class AnalyzeRequest(BaseModel):
    mode: Mode = Mode.idea
    query: str = Field(min_length=2, max_length=300)
    geography: Geography = Geography.global_
    context: Optional[str] = Field(default=None, max_length=2000)
    team_size: int = Field(default=3, ge=1, le=200)
    runway_target_months: int = Field(default=12, ge=1, le=60)
    include_darkweb: bool = True


class Section(BaseModel):
    id: str
    title: str
    icon: str = ""
    summary: str = ""
    data: dict[str, Any] = {}


class SourceOut(BaseModel):
    url: str
    kind: str = "web"
    title: str = ""


class Report(BaseModel):
    request: AnalyzeRequest
    subject: str
    sector: str = "generic"
    generated_at: str = ""
    sections: dict[str, Section] = {}
    sources: list[SourceOut] = []


@dataclass
class Evidence:
    """Raw intelligence gathered during recon, shared by every analysis agent."""

    req: AnalyzeRequest
    subject: str
    search: list[dict] = field(default_factory=list)
    wiki: dict = field(default_factory=dict)
    hn_stories: list[dict] = field(default_factory=list)
    hn_comments: list[dict] = field(default_factory=list)
    reddit: list[dict] = field(default_factory=list)
    releases: list[dict] = field(default_factory=list)
    pricing_history: list[dict] = field(default_factory=list)
    current_pricing: list[dict] = field(default_factory=list)
    reviews: list[dict] = field(default_factory=list)
    tor: dict = field(default_factory=dict)
    sector: str = "generic"
    wiki_domain_hint: str = ""
    identity: dict = field(default_factory=dict)      # triangulated subject identity
    financials: list[dict] = field(default_factory=list)  # EDGAR annual revenue history
    sources: list[SourceOut] = field(default_factory=list)

    def add_source(self, url: str, kind: str = "web", title: str = "") -> None:
        if not url or any(s.url == url for s in self.sources):
            return
        self.sources.append(SourceOut(url=url, kind=kind, title=title))

    def snippet_pool(self, limit: int = 16000) -> str:
        """Concatenated text of every scraped snippet, for keyphrase extraction."""
        chunks: list[str] = []
        for r in self.search:
            chunks.append(r.get("title", "") + " " + r.get("snippet", ""))
        if self.wiki:
            chunks.append(self.wiki.get("summary", ""))
            chunks.append(self.wiki.get("history", ""))
        for r in self.hn_stories:
            chunks.append(r.get("title", ""))
        for r in self.hn_comments:
            chunks.append(r.get("text", ""))
        for r in self.reddit:
            chunks.append(r.get("title", "") + " " + r.get("selftext", ""))
        for r in self.reviews:
            chunks.append(r.get("snippet", ""))
        for r in self.releases:
            chunks.append(r.get("name", "") + " " + r.get("body", ""))
        # ". " (not " ") so title fragments without terminal punctuation stay
        # separable sentences for the downstream n-gram/moat miners.
        text = ". ".join(c.strip() for c in chunks if c.strip())
        return text[:limit]