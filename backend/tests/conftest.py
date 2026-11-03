"""Pytest bootstrap: force deterministic offline mode BEFORE any app import.

Every test here must be reproducible with zero network access — GENESIS_OFFLINE
disables recon scraping, the Tor probe, and the Ollama bridge, and get_settings()
is lru_cached, so these variables must be set before the first import.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

os.environ["GENESIS_OFFLINE"] = "1"
os.environ["TOR_ENABLED"] = "0"

import pytest  # noqa: E402

from app.models import AnalyzeRequest, Evidence  # noqa: E402


@pytest.fixture
def req() -> AnalyzeRequest:
    return AnalyzeRequest(mode="company", query="ADP", geography="us", team_size=5)


@pytest.fixture
def ev(req: AnalyzeRequest) -> Evidence:
    """Evidence pre-loaded with one clean item per source type."""
    e = Evidence(req=req, subject="ADP")
    e.search = [{"title": "ADP payroll overview", "snippet": "ADP processes payroll for millions of workers."}]
    e.hn_stories = [{"title": "ADP developer platform launch"}]
    e.hn_comments = [{"text": "We switched to ADP and the integration was straightforward."}]
    e.reddit = [{"title": "ADP experience", "selftext": "Honestly I hate the manual spreadsheet export every single week."}]
    e.reviews = [{"snippet": "Support resolved our issue in a day."}]
    e.wiki = {"summary": "ADP charges a per-employee fee for payroll services. Founded in 1949.", "history": ""}
    return e
