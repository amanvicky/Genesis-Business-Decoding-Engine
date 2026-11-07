"""One-shot environment setup for a shared copy of Genesis.

Run by 'Genesis Setup.bat' once a usable Python 3.10+ exists (a system install
or the private copy that scripts/bootstrap_python.ps1 puts into runtime/python).
Everything else happens here, in this order:

  1. Node.js 18+  — a system install is used when present; otherwise a private
     copy is downloaded into runtime/node. No PATH edits, no registry, no admin.
  2. backend environment + frontend packages + production build — reuses
     genesis.py's idempotent installers, so a second run skips all the work.
  3. hands over to  python genesis.py up  — starts the supervised services and
     opens the dashboard as its own desktop window.

Uninstall = delete the folder. The host PC is never modified.
"""
from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime"
NODE_DIR = RUNTIME / "node"

NODE_VERSION = "20.18.1"
PYTHON_EMBED_URL = "https://www.python.org/ftp/python/3.12.8/python-3.12.8-embed-amd64.zip"
GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"
TOR_BUNDLE_URL = "https://dist.torproject.org/torbrowser/16.0/tor-expert-bundle-windows-x86_64-16.0.tar.gz"


# ---------------------------------------------------------------- pure helpers

def parse_version(text: str) -> tuple[int, ...] | None:
    """Leading dotted version out of noisy tool output ('v20.18.1', 'Python 3.13.1')."""
    m = re.search(r"(\d+(?:\.\d+)+)", text or "")
    if not m:
        return None
    return tuple(int(p) for p in m.group(1).split("."))


def version_ok(version: tuple[int, ...] | None, minimum: tuple[int, ...]) -> bool:
    if not version:
        return False
    padded = version + (0,) * (len(minimum) - len(version))
    return padded[: len(minimum)] >= minimum


def arch_tag(machine: str) -> str | None:
    """Windows download tag for this CPU, or None when we have no build."""
    m = (machine or "").upper()
    if m in ("AMD64", "X86_64"):
        return "win-x64"
    if m in ("ARM64", "AARCH64"):
        return "win-arm64"
    return None


def fix_embedded_pth(python_dir: Path) -> int:
    """Uncomment `import site` in python*._pth (embeddable pip recipe)."""
    changed = 0
    for pth in sorted(Path(python_dir).glob("python*._pth")):
        text = pth.read_text(encoding="utf-8")
        fixed = re.sub(r"^#\s*(import site)\s*$", r"\1", text, flags=re.MULTILINE)
        if fixed != text:
            pth.write_text(fixed, encoding="utf-8")
            changed += 1
    return changed


def node_zip_url(machine: str, version: str = NODE_VERSION) -> str | None:
    tag = arch_tag(machine)
    return f"https://nodejs.org/dist/v{version}/node-v{version}-{tag}.zip" if tag else None


# ------------------------------------------------------------------- plumbing

def _say(msg: str) -> None:
    print(msg, flush=True)


def download(url: str, dest: Path) -> Path:
    _say(f"[*] downloading {url.split('/')[-1]} …")
    dest.parent.mkdir(parents=True, exist_ok=True)

    def progress(blocks: int, block: int, total: int) -> None:
        if total > 0 and (blocks * block) % (5 * 1024 * 1024) < block:
            _say(f"    {min(blocks * block, total) // (1024 * 1024)} / {total // (1024 * 1024)} MB")

    urllib.request.urlretrieve(url, dest, reporthook=progress)
    return dest


def unzip_to(zip_path: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(dest)


def node_version(node_exe: str) -> tuple[int, ...] | None:
    try:
        out = subprocess.run([node_exe, "-v"], capture_output=True, text=True, timeout=30)
    except Exception:
        return None
    return parse_version(out.stdout or "") if out.returncode == 0 else None


def prepend_path(directory: Path) -> None:
    os.environ["PATH"] = f"{directory}{os.pathsep}{os.environ.get('PATH', '')}"


# ----------------------------------------------------------------- installers

def ensure_node() -> str:
    """A working Node 18+: system install if fine, else a private runtime/node.
    Returns the node executable path (and puts its dir on this process' PATH so
    the genesis.py subprocess resolves npm)."""
    if (NODE_DIR / "node.exe").exists():
        v = node_version(str(NODE_DIR / "node.exe"))
        if version_ok(v, (18, 0, 0)):
            _say(f"[OK] Node runtime ready (private copy, {'.'.join(map(str, v))})")
            prepend_path(NODE_DIR)
            return str(NODE_DIR / "node.exe")
        _say(f"[!] private Node copy is too old ({'.'.join(map(str, v or ()))}) — refreshing it")
        shutil.rmtree(NODE_DIR, ignore_errors=True)

    sys_node = shutil.which("node")
    if sys_node:
        v = node_version(sys_node)
        if version_ok(v, (18, 0, 0)):
            _say(f"[OK] Node {'.'.join(map(str, v))} found on this PC — using it as-is")
            return sys_node
        if v:
            _say(f"[*] system Node {'.'.join(map(str, v))} is too old (18+ needed) — installing a private copy instead")

    url = node_zip_url(platform.machine())
    if not url:
        raise SystemExit("[X] unsupported CPU architecture for the automatic Node install — install Node 18+ from nodejs.org")
    zip_path = download(url, Path(os.environ.get("TEMP", RUNTIME)) / f"genesis-node-{NODE_VERSION}.zip")
    tmp = RUNTIME / "node-tmp"
    shutil.rmtree(tmp, ignore_errors=True)
    _say("[*] extracting Node.js into runtime/node …")
    unzip_to(zip_path, tmp)
    inner = next((d for d in tmp.iterdir() if d.is_dir()), None)
    if inner is None:
        raise SystemExit("[X] unexpected Node archive layout")
    NODE_DIR.parent.mkdir(exist_ok=True)
    shutil.move(str(inner), str(NODE_DIR))
    shutil.rmtree(tmp, ignore_errors=True)
    zip_path.unlink(missing_ok=True)
    v = node_version(str(NODE_DIR / "node.exe"))
    if not version_ok(v, (18, 0, 0)):
        raise SystemExit("[X] private Node install did not verify — run this script again")
    _say(f"[OK] private Node {'.'.join(map(str, v))} installed into runtime/node (nothing else touched)")
    prepend_path(NODE_DIR)
    return str(NODE_DIR / "node.exe")


def ensure_tor() -> None:
    """Optional privacy layer, requested by the installer's 'tor' task (it drops
    runtime/tor-request.txt). Downloads the OFFICIAL Tor Expert Bundle from
    dist.torproject.org into runtime/tor. genesis.py launches it CLIENT-ONLY
    (SOCKS5 127.0.0.1:9050, isolated data dir) — never as a relay/exit. When
    absent, Tab 11 degrades to clearnet OSINT and says so."""
    tor_exe = RUNTIME / "tor" / "tor.exe"
    request = RUNTIME / "tor-request.txt"
    if tor_exe.exists():
        _say("[OK] private Tor client already present (runtime/tor)")
        request.unlink(missing_ok=True)
        return
    if not request.exists():
        return  # not requested — install nothing
    archive = download(TOR_BUNDLE_URL, Path(os.environ.get("TEMP", RUNTIME)) / "genesis-tor.tar.gz")
    tmp = RUNTIME / "tor-tmp"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    _say("[*] extracting the Tor client into runtime/tor …")
    import tarfile

    with tarfile.open(archive) as t:
        t.extractall(tmp)  # noqa: S202 — pinned archive from the official dist server
    hits = list(tmp.rglob("tor.exe"))
    if not hits:
        shutil.rmtree(tmp, ignore_errors=True)
        _say("[!] tor.exe missing from the bundle — skipping Tor (fully optional)")
        return
    dest = RUNTIME / "tor"
    dest.mkdir(parents=True, exist_ok=True)
    for f in hits[0].parent.iterdir():
        if f.is_file():
            shutil.copy2(f, dest / f.name)
    shutil.rmtree(tmp, ignore_errors=True)
    archive.unlink(missing_ok=True)
    request.unlink(missing_ok=True)
    _say("[OK] private Tor client installed (client-only; nothing outside this folder was touched)")


def ensure_python_pip() -> None:
    """When running under the portable embeddable python, make sure pip exists
    (bootstrap_python.ps1 normally did this — self-heal if the folder was copied)."""
    try:
        import pip  # noqa: F401
        return
    except ImportError:
        pass
    _say("[*] bootstrapping pip into the private Python …")
    gp = RUNTIME / "python" / "get-pip.py"
    download(GET_PIP_URL, gp)
    r = subprocess.run([sys.executable, str(gp), "--no-warn-script-location"], capture_output=True, text=True)
    gp.unlink(missing_ok=True)
    if r.returncode != 0:
        raise SystemExit("[X] get-pip failed:\n" + (r.stdout + r.stderr)[-2000:])
    _say("[OK] pip available in the private Python")


def main() -> int:
    if not (ROOT / "genesis.py").exists():
        raise SystemExit("[X] run this from the Genesis project (genesis.py missing next to scripts/)")
    if os.name != "nt":
        raise SystemExit("[X] this setup script targets Windows; on macOS/Linux use: python3 genesis.py up")

    _say("""
  ============================================================
   GENESIS setup — check · install privately · open the app
  ============================================================""")

    ensure_python_pip()
    ensure_node()
    ensure_tor()

    # reuse the manager's idempotent installers (venv, pip, npm, build)
    sys.path.insert(0, str(ROOT))
    import genesis  # noqa: E402

    genesis.ensure_backend_deps()
    genesis.ensure_frontend_deps()
    genesis.ensure_frontend_build(dev=False, rebuild=False)

    _say("[*] starting Genesis (supervised background services + app window) …")
    r = subprocess.run([sys.executable, str(ROOT / "genesis.py"), "up"], cwd=str(ROOT))
    if r.returncode == 0:
        _say("""
[OK] Genesis is installed and running.
   dashboard   http://localhost:3000   (its own window)
   later use   double-click 'Genesis.bat'
   stop        python genesis.py stop
   uninstall   python genesis.py uninstall --deep  (or just delete the folder)""")
    return r.returncode


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001 — a setup script must explain itself
        _say(f"[X] setup failed: {e}")
        sys.exit(1)
