from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


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

    @field_validator("query")
    @classmethod
    def _strip_and_require(cls, v: str) -> str:
        # whitespace-only queries pass min_length but strip to "" — every
        # downstream `.split()[0]` then explodes and recon silently dies
        v = v.strip()
        if len(v) < 2:
            raise ValueError("query must be at least 2 characters after trimming")
        return v
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
        def _join(*parts: str) -> str:
            # Fields must be joined as separate sentences (". " not " "): a title
            # without terminal punctuation fused to its snippet once glued the
            # two into one pseudo-sentence, defeating both sentence-splitting
            # and the sentence-level dedupe key below.
            return ". ".join(p.strip() for p in parts if p and p.strip())

        chunks: list[str] = []
        for r in self.search:
            chunks.append(_join(r.get("title", ""), r.get("snippet", "")))
        if self.wiki:
            chunks.append(_join(self.wiki.get("summary", "")))
            chunks.append(_join(self.wiki.get("history", "")))
        for r in self.hn_stories:
            chunks.append(_join(r.get("title", "")))
        for r in self.hn_comments:
            chunks.append(_join(r.get("text", "")))
        for r in self.reddit:
            chunks.append(_join(r.get("title", ""), r.get("selftext", "")))
        for r in self.reviews:
            chunks.append(_join(r.get("snippet", "")))
        for r in self.releases:
            chunks.append(_join(r.get("name", ""), r.get("body", "")))
        # Sentence-level dedupe: the same story often arrives from two engines
        # and duplicated text poisons every downstream miner.
        seen_sentences: set[str] = set()
        cleaned: list[str] = []
        # collapse a phrase repeated back-to-back inside one snippet
        # ("PNC and ADP integrate payroll tools PNC and ADP integrate payroll tools")
        repeat = re.compile(r"\b((?:\w+\s+){4,}\w+)\s+\1\b")
        for chunk in chunks:
            for sentence in re.split(r"(?<=[.!?])\s+", chunk.strip()):
                sentence = repeat.sub(r"\1", sentence)
                key = sentence.strip().lower()[:140]
                if not key or key in seen_sentences:
                    continue
                seen_sentences.add(key)
                cleaned.append(sentence.strip())
        text = ". ".join(cleaned)
        return text[:limit]