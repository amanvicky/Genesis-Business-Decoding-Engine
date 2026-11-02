from __future__ import annotations

import time
from typing import Any, Awaitable, Callable

from ..llm import enrich
from ..models import Evidence, Section

Emit = Callable[[dict], Awaitable[None]]


class Agent:
    id: str = ""
    title: str = ""
    icon: str = ""
    tab: int = 0  # 1-based tab order in the report viewer

    async def run(self, ev: Evidence, emit: Emit, sections: dict | None = None) -> None:
        # Cross-section agents (e.g. the adversary) read the sections built so far.
        self.sections: dict = sections or {}
        await emit({"type": "status", "step": self.tab, "agent": self.id, "state": "running", "title": self.title})
        t0 = time.perf_counter()
        try:
            data = await self.build(ev)
            summary = self.summarize(ev, data)
        except Exception as exc:  # never kill the whole report for one tab
            await emit({"type": "log", "level": "error", "agent": self.id, "msg": f"failed: {type(exc).__name__}: {exc}"})
            data = {"error": f"Section failed to build: {type(exc).__name__}: {exc}", "partial": True}
            summary = "This section hit an error while building; re-run or check backend logs."
            section = Section(id=self.id, title=self.title, icon=self.icon, summary=summary, data=data)
            await emit({"type": "section", "section": section.model_dump()})
            await emit({"type": "status", "step": self.tab, "agent": self.id, "state": "failed", "title": self.title})
            return

        # Optional zero-cost LLM sharpening (skipped entirely when Ollama is absent)
        prompt = self.llm_prompt(ev, data)
        if prompt:
            await emit({"type": "log", "level": "info", "agent": self.id, "msg": "checking for local LLM (Ollama)…"})
            insight = await enrich(prompt, ev.snippet_pool())
            if insight:
                data = dict(data)
                data["ai_insight"] = insight
                await emit({"type": "log", "level": "success", "agent": self.id, "msg": "narrative sharpened by local LLM"})

        section = Section(id=self.id, title=self.title, icon=self.icon, summary=summary, data=data)
        await emit({"type": "section", "section": section.model_dump()})
        await emit({"type": "status", "step": self.tab, "agent": self.id, "state": "done", "title": self.title, "ms": int((time.perf_counter() - t0) * 1000)})

    # -- subclasses implement -------------------------------------------
    async def build(self, ev: Evidence) -> dict[str, Any]:
        raise NotImplementedError

    def summarize(self, ev: Evidence, data: dict[str, Any]) -> str:
        return ""

    def llm_prompt(self, ev: Evidence, data: dict[str, Any]) -> str:
        return ""
