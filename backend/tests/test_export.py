"""Exporter contract: Markdown rendering, schema-versioned JSON, ZIP contents,
and hostile payload handling (path traversal in scaffold, weird shapes)."""
from __future__ import annotations

import io
import json
import zipfile

from app import export


def _minimal_report() -> dict:
    return {
        "request": {"mode": "company", "geography": "us"},
        "subject": "ADP",
        "sector": "payroll",
        "generated_at": "2026-11-03T00:00:00+00:00",
        "sections": {
            "structural": {
                "id": "structural",
                "title": "Structural Feasibility & Core Mechanics",
                "summary": "A | tricky summary",
                "data": {
                    "pain_points": [
                        {"source": "reddit", "text": "row with a | pipe and\nnewline", "url": "https://x.com"}
                    ],
                    "verdict_score": 55,
                },
            }
        },
        "sources": [{"url": "https://example.com", "kind": "web", "title": "Example"}],
    }


class TestMarkdown:
    def test_headers_and_subject(self):
        md = export.report_to_markdown(_minimal_report())
        assert md.startswith("# Genesis Decoding Report — ADP")
        assert "Structural Feasibility & Core Mechanics" in md

    def test_table_cells_escaped(self):
        md = export.report_to_markdown(_minimal_report())
        # summary renders as a blockquote (pipes unescaped there)
        assert "> A | tricky summary" in md
        # but table cells must escape pipes/newlines or the table breaks
        assert "row with a \\| pipe and newline" in md

    def test_sources_appendix_and_disclaimer(self):
        md = export.report_to_markdown(_minimal_report())
        assert "## Appendix — Evidence Sources" in md
        assert "https://example.com" in md
        assert "Not legal, financial, or tax advice." in md

    def test_only_known_tabs_rendered_in_order(self):
        report = _minimal_report()
        report["sections"]["zzz-unknown"] = {"id": "zzz-unknown", "title": "Ghost", "data": {}}
        md = export.report_to_markdown(report)
        assert "Ghost" not in md  # unknown section ids are skipped

    def test_empty_report_does_not_crash(self):
        md = export.report_to_markdown({})
        assert "Unknown" in md


class TestJson:
    def test_schema_and_roundtrip(self):
        blob = export.report_to_json(_minimal_report())
        payload = json.loads(blob)
        assert payload["schema"] == "genesis.report/v1"
        assert payload["report"]["subject"] == "ADP"

    def test_weird_values_never_crash(self):
        blob = export.report_to_json({"subject": "x", "sections": {"structural": {"data": {"when": "2026-01-01"}}}})
        assert json.loads(blob)["report"]["subject"] == "x"


class TestZip:
    def _names(self, report: dict) -> list[str]:
        zf = zipfile.ZipFile(io.BytesIO(export.report_to_zip(report)))
        return zf.namelist()

    def test_core_members(self):
        names = self._names(_minimal_report())
        assert names[:3] == ["GENESIS_REPORT.md", "GENESIS_REPORT.json", "manifest.json"]

    def test_manifest_lists_sections(self):
        zf = zipfile.ZipFile(io.BytesIO(export.report_to_zip(_minimal_report())))
        manifest = json.loads(zf.read("manifest.json"))
        assert manifest["subject"] == "ADP"
        assert manifest["sections"] == ["structural"]

    def test_scaffold_included(self):
        report = _minimal_report()
        report["sections"]["techarch"] = {
            "id": "techarch", "title": "Tech", "data": {"files": [{"path": "backend/main.py", "content": "print('hi')"}]}
        }
        zf = zipfile.ZipFile(io.BytesIO(export.report_to_zip(report)))
        assert "scaffold/backend/main.py" in zf.namelist()
        assert zf.read("scaffold/backend/main.py") == b"print('hi')"

    def test_scaffold_path_traversal_neutralized(self):
        report = _minimal_report()
        report["sections"]["techarch"] = {
            "id": "techarch", "title": "Tech",
            "data": {"files": [
                {"path": "../../evil.txt", "content": "boom"},
                {"path": "..\\..\\win_evil.txt", "content": "boom"},
                {"path": "/abs/path.txt", "content": "ok"},
            ]},
        }
        names = self._names(report)
        assert all(".." not in n for n in names)
        assert all("\\" not in n for n in names)
        assert not any(n.startswith("/") for n in names)

    def test_scaffold_non_dict_entries_skipped(self):
        report = _minimal_report()
        report["sections"]["techarch"] = {
            "id": "techarch", "title": "Tech", "data": {"files": ["not-a-dict", None, 42]}
        }
        names = self._names(report)  # must not raise
        assert not any(n.startswith("scaffold/") for n in names)

    def test_scaffold_files_not_a_list(self):
        report = _minimal_report()
        report["sections"]["techarch"] = {"id": "techarch", "title": "Tech", "data": {"files": {"path": "x"}}}
        self._names(report)  # must not raise

    def test_zip_is_valid_zip(self):
        assert export.report_to_zip(_minimal_report())[:2] == b"PK"
