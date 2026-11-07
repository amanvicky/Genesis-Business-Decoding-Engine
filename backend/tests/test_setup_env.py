"""Pure helpers of the Windows installer toolchain (scripts/setup_env.py,
scripts/fix_pth.py). Loaded by path — these live outside the backend package
on purpose: the installer runs before any venv exists."""
import importlib.util
import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


setup_env = _load("setup_env")
fix_pth = _load("fix_pth")


class TestParseVersion:
    @pytest.mark.parametrize("text,expected", [
        ("v20.18.1", (20, 18, 1)),
        ("Python 3.13.1", (3, 13, 1)),
        ("3.10", (3, 10)),
        ("", None),
        ("garbage output", None),
        ("v", None),
    ])
    def test_parsing(self, text, expected):
        assert setup_env.parse_version(text) == expected


class TestVersionOk:
    def test_minimum_padded_comparison(self):
        assert setup_env.version_ok((20, 18, 1), (18, 0)) is True
        assert setup_env.version_ok((17, 9, 9), (18, 0)) is False
        assert setup_env.version_ok((3, 10), (3, 10, 0)) is True  # padded, not truncated
        assert setup_env.version_ok(None, (18, 0)) is False


class TestArch:
    def test_windows_download_tags(self):
        assert setup_env.arch_tag("AMD64") == "win-x64"
        assert setup_env.arch_tag("x86_64") == "win-x64"
        assert setup_env.arch_tag("ARM64") == "win-arm64"
        assert setup_env.arch_tag("i686") is None
        assert setup_env.node_zip_url("AMD64").endswith("node-v20.18.1-win-x64.zip")
        assert setup_env.node_zip_url("i686") is None


class TestFixEmbeddedPth:
    def test_uncomments_import_site_once(self, tmp_path):
        pth = tmp_path / "python312._pth"
        pth.write_text("python312.zip\n.\n#import site\n", encoding="utf-8")
        assert setup_env.fix_embedded_pth(tmp_path) == 1
        assert "#import site" not in pth.read_text(encoding="utf-8")
        assert "import site" in pth.read_text(encoding="utf-8")
        # idempotent
        assert setup_env.fix_embedded_pth(tmp_path) == 0

    def test_no_pth_files_is_a_noop(self, tmp_path):
        assert setup_env.fix_embedded_pth(tmp_path) == 0


class TestFixPthScript:
    def test_shipped_fixer_matches_helper(self, tmp_path):
        pth = tmp_path / "python313._pth"
        pth.write_text("python313.zip\n.\n# import site\n", encoding="utf-8")
        assert fix_pth.fix_dir(tmp_path) == 1
        assert "import site" in pth.read_text(encoding="utf-8")

    def test_shipped_fixer_ignores_unrelated_files(self, tmp_path):
        (tmp_path / "readme._pth.bak").write_text("#import site\n", encoding="utf-8")
        assert fix_pth.fix_dir(tmp_path) == 0
