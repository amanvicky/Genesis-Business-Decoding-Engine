#!/usr/bin/env python3
"""Genesis service manager — install, run, supervise, stop. One command.

Everything runs DETACHED in the background (survives terminal close) under a
watchdog that restarts crashed services automatically:

    python genesis.py                 # up: install what's missing, start all, open browser
    python genesis.py up --dev        # hot-reload dev mode instead of production
    python genesis.py up --no-tor     # skip the safe Tor client
    python genesis.py up --rebuild    # force a fresh frontend production build
    python genesis.py status          # what is running, healthy, on which port
    python genesis.py logs api        # tail api|web|tor|watchdog logs
    python genesis.py stop            # stop everything this manager started
    python genesis.py restart         # stop + up
    python genesis.py doctor          # pre-flight diagnostic report

Safety model for Tor: this manager only ever LAUNCHES an already-installed Tor
binary as a plain client (SOCKS5 on 127.0.0.1:9050, isolated data directory).
It never downloads Tor, never configures relays/exit nodes or hidden services.
If Tor is absent the platform runs fine without it (Tab 11 degrades to
clearnet OSINT and says so).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

IS_WIN = os.name == "nt"
ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / "runtime"
LOGS = ROOT / "logs"
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
API_PORT, WEB_PORT, TOR_PORT = 8000, 3000, 9050
API_URL = f"http://127.0.0.1:{API_PORT}"
WEB_URL = f"http://127.0.0.1:{WEB_PORT}"
TOR_PROXY = f"socks5://127.0.0.1:{TOR_PORT}"

SERVICES_JSON = RUNTIME / "services.json"
WATCHDOG_STATE = RUNTIME / "watchdog_state.json"

if IS_WIN:
    os.system("")  # enable ANSI escape processing in legacy consoles

C = {"g": "\033[92m", "y": "\033[93m", "r": "\033[91m", "b": "\033[96m", "d": "\033[90m", "0": "\033[0m", "B": "\033[1m"}


def info(msg: str) -> None:
    print(f"{C['b']}[*]{C['0']} {msg}", flush=True)


def ok(msg: str) -> None:
    print(f"{C['g']}[OK]{C['0']} {msg}", flush=True)


def warn(msg: str) -> None:
    print(f"{C['y']}[!]{C['0']} {msg}", flush=True)


def err(msg: str) -> None:
    print(f"{C['r']}[X]{C['0']} {msg}", flush=True)


def die(msg: str, code: int = 1) -> None:
    err(msg)
    sys.exit(code)


def banner() -> None:
    print(f"""{C['B']}
  ============================================================
   GENESIS service manager  —  install · run · supervise · stop
  ============================================================{C['0']}""")


# ---------------------------------------------------------------- primitives

def port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.6)
        return s.connect_ex(("127.0.0.1", port)) == 0


def http_ok(url: str, timeout: float = 3.0) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return 200 <= r.status < 400
    except Exception:
        return False


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if IS_WIN:
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True).stdout.lower()
        return str(pid) in out
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def kill_tree(pid: int) -> None:
    if IS_WIN:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True, text=True)
    else:
        import signal

        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            return
        for _ in range(30):
            if not pid_alive(pid):
                return
            time.sleep(0.1)
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass


def proc_identity(pid: int) -> tuple[str, str]:
    """(command line, executable path) — either may reveal project ownership
    (old instances were started with relative command lines)."""
    try:
        if IS_WIN:
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 f"$p=Get-CimInstance Win32_Process -Filter 'ProcessId={pid}'; \"$($p.CommandLine)||$($p.ExecutablePath)\""],
                capture_output=True, text=True, timeout=15).stdout
            cmdline, _, exepath = (out or "").strip().partition("||")
            return cmdline.strip(), exepath.strip()
        cmdline = Path(f"/proc/{pid}/cmdline").read_bytes().decode(errors="replace").replace("\x00", " ")
        exe = ""
        try:
            exe = os.readlink(f"/proc/{pid}/exe")
        except OSError:
            pass
        return cmdline, exe
    except Exception:
        return "", ""


def is_ours(pid: int) -> bool:
    """Ownership test: project path in cmdline/exe, or an unmistakable service
    signature (this app's uvicorn module path, Next's dist launcher). Only ever
    combined with 'holds one of our ports', so collateral damage is impossible."""
    root_low = str(ROOT).lower()
    cmdline, exepath = proc_identity(pid)
    blob = f"{cmdline} {exepath}".lower()
    if root_low in blob:
        return True
    return "app.main:app" in blob or ("next" in blob and ("dist\\bin" in blob or "dist/bin" in blob))


def listeners_on(port: int) -> set[int]:
    """PIDs currently listening on the port (best effort)."""
    pids: set[int] = set()
    try:
        if IS_WIN:
            out = subprocess.run(["netstat", "-ano", "-p", "TCP"], capture_output=True, text=True).stdout
            for line in out.splitlines():
                parts = line.split()
                if len(parts) >= 5 and f":{port}" in parts[1] and parts[3].upper() == "LISTENING":
                    try:
                        pids.add(int(parts[4]))
                    except ValueError:
                        pass
        else:
            out = subprocess.run(["lsof", "-t", "-i", f"TCP:{port}", "-s", "TCP:LISTEN"], capture_output=True, text=True).stdout
            pids = {int(x) for x in out.split() if x.strip().isdigit()}
    except Exception:
        pass
    return pids


def read_pid(name: str) -> int:
    p = RUNTIME / f"{name}.pid"
    try:
        return int(p.read_text().strip())
    except Exception:
        return 0


def write_pid(name: str, pid: int) -> None:
    RUNTIME.mkdir(exist_ok=True)
    (RUNTIME / f"{name}.pid").write_text(str(pid))


def spawn(name: str, cmd: list[str], cwd: Path, logfile: str) -> int:
    """Launch a detached background process with output to a log file."""
    LOGS.mkdir(exist_ok=True)
    RUNTIME.mkdir(exist_ok=True)
    log = open(LOGS / logfile, "ab", buffering=0)
    log.write(f"\n===== spawn {name} {time.strftime('%Y-%m-%d %H:%M:%S')} :: {' '.join(cmd)}\n".encode())
    kwargs: dict = {}
    if IS_WIN:
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    proc = subprocess.Popen(cmd, cwd=str(cwd), stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, **kwargs)
    write_pid(name, proc.pid)
    return proc.pid


def resolve_real_pid(name: str, port: int, timeout: float = 40.0) -> int:
    """Track the REAL server process. Windows venv launchers and npm re-exec
    into children, so the spawned pid is often just a launcher that dies while
    its child keeps serving. Poll the port until someone binds, then record
    that pid — stop/watchdog kill the whole generation, not just the launcher."""
    deadline = time.time() + timeout
    launcher = read_pid(name)
    while time.time() < deadline:
        for pid in listeners_on(port):
            if pid != launcher:
                (RUNTIME / f"{name}.real.pid").write_text(str(pid))
                return pid
        if not pid_alive(launcher):
            break
        time.sleep(0.5)
    (RUNTIME / f"{name}.real.pid").unlink(missing_ok=True)
    return 0


def kill_generation(name: str, port: int) -> None:
    """Kill the launcher, the real server, and any project-owned orphan on the port."""
    for pid_file in (name, f"{name}.real"):
        pid = read_pid(pid_file)
        if pid and pid_alive(pid):
            kill_tree(pid)
    for pid in listeners_on(port):
        if is_ours(pid):
            kill_tree(pid)
    (RUNTIME / f"{name}.pid").unlink(missing_ok=True)
    (RUNTIME / f"{name}.real.pid").unlink(missing_ok=True)


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stale_marker_ok(marker: str, *sources: Path) -> bool:
    """Marker file holds hashes of the sources; True when all still match."""
    p = RUNTIME / marker
    if not p.exists():
        return False
    try:
        saved = json.loads(p.read_text())
    except Exception:
        return False
    return all(saved.get(s.name) == sha256_of(s) for s in sources)


def write_marker(marker: str, *sources: Path) -> None:
    RUNTIME.mkdir(exist_ok=True)
    (RUNTIME / marker).write_text(json.dumps({s.name: sha256_of(s) for s in sources}))


def find_python() -> str:
    for cand in (shutil.which("python3"), shutil.which("python"), shutil.which("py")):
        if cand:
            return cand
    return sys.executable


def venv_python() -> Path:
    return BACKEND / ".venv" / ("Scripts/python.exe" if IS_WIN else "bin/python")


def npm() -> str:
    n = shutil.which("npm")
    if not n:
        die("npm not found — install Node.js 18+ from https://nodejs.org then re-run")
    return n


# ------------------------------------------------------------- port takeover

def free_project_ports(ports: tuple[int, ...]) -> list[str]:
    """Kill processes on our ports ONLY if they belong to this project
    (ownership via project path or unmistakable service signature) — never
    foreign apps. Returns the ports that had to be cleared."""
    freed: list[str] = []
    for port in ports:
        name = {API_PORT: "api", WEB_PORT: "web"}.get(port, "x")
        before = port_open(port)
        kill_generation(name, port)
        time.sleep(1.0)
        if before and not port_open(port):
            freed.append(str(port))
        for pid in listeners_on(port):
            if is_ours(pid):
                kill_tree(pid)
                time.sleep(0.8)
                freed.append(str(port))
            else:
                warn(f"port {port} is held by a FOREIGN process (pid {pid}) — leaving it alone")
    return freed


# ------------------------------------------------------------------- setup

def ensure_backend_deps() -> None:
    reqs = BACKEND / "requirements.txt"
    vp = venv_python()
    if vp.exists() and stale_marker_ok("pip.stamp", reqs):
        ok("backend environment ready (already installed)")
        return
    info("installing backend environment (first run or requirements changed)…")
    if not vp.exists():
        subprocess.run([find_python(), "-m", "venv", str(BACKEND / ".venv")], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    r = subprocess.run([str(vp), "-m", "pip", "install", "--disable-pip-version-check", "-q", "-r", str(reqs)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        (LOGS / "setup.log").write_text(r.stdout + r.stderr)
        die("backend pip install failed — see logs/setup.log")
    write_marker("pip.stamp", reqs)
    ok("backend environment installed")


def ensure_frontend_deps() -> None:
    pkg, lock = FRONTEND / "package.json", FRONTEND / "package-lock.json"
    if (FRONTEND / "node_modules").exists() and stale_marker_ok("npm.stamp", pkg, lock):
        ok("frontend packages ready (already installed)")
        return
    info("installing frontend packages (1–3 min on first run)…")
    r = subprocess.run([npm(), "install", "--no-audit", "--no-fund"], cwd=str(FRONTEND),
                       capture_output=True, text=True)
    if r.returncode != 0:
        (LOGS / "setup.log").write_text(r.stdout + r.stderr)
        die("npm install failed — see logs/setup.log")
    write_marker("npm.stamp", pkg, lock)
    ok("frontend packages installed")


def frontend_sources_freshness() -> float:
    newest = 0.0
    for base in ("app", "components", "lib", "public"):
        d = FRONTEND / base
        if d.exists():
            newest = max(newest, max((f.stat().st_mtime for f in d.rglob("*") if f.is_file()), default=0.0))
    for f in ("package.json", "next.config.mjs", "tailwind.config.ts", "tsconfig.json", "postcss.config.mjs"):
        p = FRONTEND / f
        if p.exists():
            newest = max(newest, p.stat().st_mtime)
    return newest


def ensure_frontend_build(dev: bool, rebuild: bool) -> None:
    if dev:
        ok("dev mode selected — skipping production build")
        return
    build_id = FRONTEND / ".next" / "BUILD_ID"
    stamp = RUNTIME / "build.stamp"
    fresh = stamp.exists() and stamp.stat().st_mtime >= frontend_sources_freshness() and build_id.exists()
    if fresh and not rebuild:
        ok("frontend production build ready (up to date)")
        return
    info("building frontend production bundle (1–2 min)…")
    r = subprocess.run([npm(), "run", "build"], cwd=str(FRONTEND), capture_output=True, text=True)
    if r.returncode != 0:
        (LOGS / "setup.log").write_text(r.stdout[-8000:] + r.stderr[-8000:])
        die("frontend build failed — see logs/setup.log (or run: python genesis.py up --dev)")
    stamp.write_text(str(time.time()))
    ok("frontend production build complete")


# ---------------------------------------------------------------------- tor

def find_tor_binary() -> str | None:
    exe = "tor.exe" if IS_WIN else "tor"
    candidates = [
        shutil.which("tor"),
        r"C:\Program Files\Tor\tor.exe" if IS_WIN else None,
        str(Path.home() / "Desktop" / "Tor Browser" / "Browser" / "Tor" / "tor.exe") if IS_WIN else None,
        "/usr/bin/tor", "/usr/sbin/tor", "/usr/local/bin/tor", "/opt/homebrew/bin/tor",
    ]
    for c in candidates:
        if c and Path(c).exists():
            return c
    return None


def ensure_tor(enabled: bool) -> None:
    if port_open(TOR_PORT):
        ok(f"Tor SOCKS5 already listening on 127.0.0.1:{TOR_PORT} (external)")
        RUNTIME.mkdir(exist_ok=True)
        (RUNTIME / "tor.pid").write_text("0")  # external, not ours to manage
        return
    if not enabled:
        warn("Tor disabled (--no-tor) — Dark-Web module will use clearnet OSINT")
        return
    tor_bin = find_tor_binary()
    if not tor_bin:
        warn("Tor is not installed — continuing without it (100% optional)")
        warn("  install later: https://www.torproject.org/download/tor/ (Expert Bundle)")
        warn("  then re-run: python genesis.py   (manager will start it as a safe client)")
        return
    data_dir = RUNTIME / "tor-data"
    data_dir.mkdir(exist_ok=True)
    pid = spawn("tor", [tor_bin, "--SocksPort", f"127.0.0.1:{TOR_PORT}",
                        "--DataDirectory", str(data_dir), "--ClientOnly", "1"], ROOT, "tor.log")
    ok(f"safe Tor client started (pid {pid}, SOCKS5 127.0.0.1:{TOR_PORT}, client-only)")
    warn("  bootstrapping may take ~10–60s; Tab 11 uses it as soon as it's ready")


# ------------------------------------------------------------------ health

def wait_healthy(url: str, name: str, timeout: float = 90.0) -> bool:
    info(f"waiting for {name} at {url} …")
    deadline = time.time() + timeout
    while time.time() < deadline:
        if http_ok(url):
            ok(f"{name} is healthy")
            return True
        time.sleep(1.0)
    return False


def ollama_status() -> tuple[bool, str]:
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=2) as r:
            models = json.load(r).get("models") or []
        names = [m.get("name", "?") for m in models[:3]]
        return True, ", ".join(names) if names else "no models pulled"
    except Exception:
        return False, "not running (optional)"


# ------------------------------------------------------------- commands

def cmd_up(args: argparse.Namespace) -> None:
    banner()
    if not BACKEND.exists() or not FRONTEND.exists():
        die("run this from the Genesis project root (backend/ and frontend/ must exist)")

    if http_ok(f"{API_URL}/api/health") and http_ok(WEB_URL):
        ok("Genesis is ALREADY RUNNING — nothing to do")
        warn(f"  dashboard: {WEB_URL}   |   stop: python genesis.py stop")
        cmd_status()
        return

    # 1. prerequisites
    info("[1/6] checking prerequisites…")
    ensure_backend_deps()
    ensure_frontend_deps()

    # 2. port takeover (only processes belonging to this project)
    info("[2/6] clearing project ports…")
    free_project_ports((API_PORT, WEB_PORT))

    # 3. frontend build
    info("[3/6] preparing frontend…")
    ensure_frontend_build(dev=args.dev, rebuild=args.rebuild)

    # 4. safe Tor client (optional layer)
    info("[4/6] Tor layer…")
    ensure_tor(enabled=not args.no_tor)

    # 5. launch backend + frontend detached
    info("[5/6] launching services in the background…")
    services = {
        "api": {"cmd": [str(venv_python()), "-m", "uvicorn", "app.main:app", "--port", str(API_PORT)],
                "cwd": str(BACKEND), "log": "api.log", "url": f"{API_URL}/api/health"},
        "web": {"cmd": [npm(), "run", "dev" if args.dev else "start"],
                "cwd": str(FRONTEND), "log": "web.log", "url": WEB_URL},
    }
    api_pid = spawn("api", services["api"]["cmd"], BACKEND, "api.log")
    web_pid = spawn("web", services["web"]["cmd"], FRONTEND, "web.log")
    real_api = resolve_real_pid("api", API_PORT, timeout=45)
    real_web = resolve_real_pid("web", WEB_PORT, timeout=60)
    ok(f"api  pid {api_pid}" + (f", server {real_api}" if real_api else "") + " → logs/api.log")
    ok(f"web  pid {web_pid}" + (f", server {real_web}" if real_web else "") + " → logs/web.log")

    # 6. watchdog: restarts crashed services automatically
    if not args.no_watchdog:
        SERVICES_JSON.write_text(json.dumps(services, indent=2))
        WATCHDOG_STATE.unlink(missing_ok=True)  # fresh run = fresh restart budget
        wd = spawn("watchdog", [sys.executable, str(Path(__file__).resolve()), "_watchdog"], ROOT, "watchdog.log")
        ok(f"watchdog pid {wd} — crashed services are restarted automatically")

    # healthy gates
    api_ok = wait_healthy(services["api"]["url"], "API server")
    web_ok = wait_healthy(services["web"]["url"], "Web dashboard", timeout=120)
    if not (api_ok and web_ok):
        warn("something is not healthy yet — check: python genesis.py logs api|web")
        warn("the watchdog keeps retrying; nothing is lost by closing this window")

    cmd_status()
    if args.browser and api_ok and web_ok:
        info("opening dashboard in your browser…")
        webbrowser.open(WEB_URL)
    print(f"""
{C['B']}  [GENESIS IS RUNNING IN THE BACKGROUND]{C['0']}
   dashboard   {WEB_URL}
   api docs    {API_URL}/docs
   status      python genesis.py status
   logs        python genesis.py logs api
   stop        python genesis.py stop

   {C['d']}safe to close this window — services stay up (watchdog supervised){C['0']}""")


def cmd_stop(args: argparse.Namespace) -> None:
    stopped = []
    for name in ("watchdog", "web", "api", "tor"):
        pid = read_pid(name)
        if pid and pid_alive(pid):
            info(f"stopping {name} (pid {pid})…")
            kill_tree(pid)
            stopped.append(name)
        (RUNTIME / f"{name}.pid").unlink(missing_ok=True)
    freed = free_project_ports((API_PORT, WEB_PORT))
    if freed:
        ok(f"freed stale project processes on: {', '.join(freed)}")
    if stopped or freed:
        ok(f"all background services are down (stopped: {', '.join(stopped) or 'none'})")
    else:
        ok("nothing was running")


def _parent_map() -> dict[int, int]:
    """pid → parent pid (best effort)."""
    out: dict[int, int] = {}
    try:
        if IS_WIN:
            r = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId | ConvertTo-Csv -NoTypeInformation"],
                capture_output=True, text=True, timeout=40)
            for line in r.stdout.splitlines()[1:]:
                parts = line.strip().strip('"').split('","')
                if len(parts) == 2:
                    try:
                        out[int(parts[0])] = int(parts[1])
                    except ValueError:
                        pass
        else:
            for p in Path("/proc").glob("[0-9]*"):
                try:
                    out[int(p.name)] = int((p / "stat").read_text().split()[3])
                except Exception:
                    pass
    except Exception:
        pass
    return out


def service_owns_port(tracked: int, port: int) -> bool:
    """True when the tracked service (or a direct descendant — Windows venv
    launchers and npm re-exec into children) actually serves the port."""
    listeners = listeners_on(port)
    if not listeners:
        return False
    if tracked in listeners:
        return True
    parents = _parent_map()
    for lid in listeners:
        cur, hops = lid, 0
        while cur and hops < 6:
            cur = parents.get(cur, 0)
            if cur == tracked:
                return True
            hops += 1
    return False


def cmd_status(args: argparse.Namespace | None = None) -> None:
    rows = []
    for name, port, url in (("api", API_PORT, f"{API_URL}/api/health"), ("web", WEB_PORT, WEB_URL)):
        pid = read_pid(name)
        alive = bool(pid and pid_alive(pid))
        healthy = http_ok(url)
        rows.append((name, f"pid {pid}" if alive else ("external" if port_open(port) else "down"),
                     "healthy" if healthy else ("unhealthy" if port_open(port) else "down")))
    tor_pid = read_pid("tor")
    if tor_pid == 0 and port_open(TOR_PORT):
        tor_state = "external"
    elif tor_pid and pid_alive(tor_pid):
        tor_state = "running (ours)"
    else:
        tor_state = "off"
    llm_ok, llm_detail = ollama_status()
    print(f"""
  {C['B']}service     state        health{C['0']}
  api         {rows[0][1]:<12} {rows[0][2]}
  web         {rows[1][1]:<12} {rows[1][2]}
  tor         {tor_state:<12} {'socks5 127.0.0.1:%d' % TOR_PORT if tor_state != 'off' else '—'}
  ollama      {'running' if llm_ok else 'off':<12} {llm_detail}
  dashboard   {WEB_URL}   |   api docs   {API_URL}/docs""")


def cmd_logs(args: argparse.Namespace) -> None:
    path = LOGS / f"{args.service}.log"
    if not path.exists():
        die(f"no log yet: {path}")
    lines = path.read_text(errors="replace").splitlines()
    for ln in lines[-args.lines:]:
        print(ln)


def cmd_doctor(args: argparse.Namespace) -> None:
    banner()
    checks: list[tuple[str, bool, str]] = []

    def add(name: str, passed: bool, detail: str = "") -> None:
        checks.append((name, passed, detail))

    py = f"{sys.version_info.major}.{sys.version_info.minor}"
    add(f"python {py}", sys.version_info >= (3, 10), "3.10+ required")
    node = shutil.which("node")
    node_ver = subprocess.run([node, "-v"], capture_output=True, text=True).stdout.strip() if node else ""
    add("node", bool(node), node_ver or "18+ required from nodejs.org")
    add(f"backend venv", venv_python().exists(), "auto-created on first 'up'")
    add("frontend packages", (FRONTEND / "node_modules").exists(), "auto-installed on first 'up'")
    add("frontend production build", (FRONTEND / ".next" / "BUILD_ID").exists(), "auto-built on first 'up'")
    for port, svc in ((API_PORT, "api"), (WEB_PORT, "web")):
        if port_open(port):
            pid_holders = listeners_on(port)
            ours = any(str(ROOT).lower() in proc_cmdline(p).lower() for p in pid_holders)
            add(f"port {port} ({svc})", True, "held by this project" if ours else "held by a foreign process — will not be touched")
        else:
            add(f"port {port} ({svc})", True, "free")
    add("tor binary", find_tor_binary() is not None, find_tor_binary() or "optional — Tab 11 degrades gracefully")
    add("tor proxy live", port_open(TOR_PORT), f"socks5://127.0.0.1:{TOR_PORT}" if port_open(TOR_PORT) else "optional")
    llm_ok, llm_detail = ollama_status()
    add("ollama (local LLM)", llm_ok, llm_detail)

    hard_fail = False
    for name, passed, detail in checks:
        mark = f"{C['g']}✓{C['0']}" if passed else f"{C['r']}✗{C['0']}"
        if name.startswith(("python", "node")) and not passed:
            hard_fail = True
        print(f"  {mark} {name:<28} {C['d']}{detail}{C['0']}")
    print()
    if hard_fail:
        die("fix the ✗ prerequisites above, then re-run", 2)
    ok("doctor: ready — run  python genesis.py  to launch everything in the background")


def cmd_watchdog(args: argparse.Namespace) -> None:
    """Resident supervisor: restarts our services if their ports go dead.
    Bounded restarts (10 per service per hour) so a broken build can't loop."""
    info(f"watchdog online (pid {os.getpid()}) — supervising api:{API_PORT} web:{WEB_PORT}")
    state = {"restarts": {}}
    if WATCHDOG_STATE.exists():
        try:
            saved = json.loads(WATCHDOG_STATE.read_text())
            if time.time() - saved.get("ts", 0) < 3600:
                state = saved
        except Exception:
            pass
    while True:
        time.sleep(10)
        try:
            services = json.loads(SERVICES_JSON.read_text())
        except Exception:
            continue
        for name, spec in services.items():
            port = API_PORT if name == "api" else WEB_PORT
            tracked = read_pid(name)
            if tracked == 0:
                continue  # manager stopped us deliberately
            healthy = http_ok(spec["url"], timeout=2.0)
            tracked_owns = service_owns_port(tracked, port) if healthy else False
            if healthy and tracked_owns:
                continue
            window = state["restarts"].setdefault(name, [])
            window[:] = [t for t in window if time.time() - t < 3600]
            if len(window) >= 10:
                if not state.get(f"{name}_limited"):
                    state[f"{name}_limited"] = True
                    WATCHDOG_STATE.write_text(json.dumps(state))
                    warn(f"watchdog: {name} hit the restart limit (10/hour) — service stays down; run 'python genesis.py' to reset")
                continue
            window.append(time.time())
            state["restarts"] = state.get("restarts", {})
            state["ts"] = time.time()
            WATCHDOG_STATE.write_text(json.dumps(state))
            if healthy and not tracked_owns:
                warn(f"watchdog: {name} port healthy but held by an orphan (tracked pid {tracked}) — reclaiming")
            else:
                warn(f"watchdog: {name} is down — restarting (attempt {len(window)}/10 this hour)")
            # kill the whole generation: launcher + real server + port orphans
            kill_generation(name, port)
            time.sleep(2.0)
            spawn(name, spec["cmd"], Path(spec["cwd"]), spec["log"])
            resolve_real_pid(name, port, timeout=60)


def main() -> None:
    parser = argparse.ArgumentParser(prog="genesis", description="Genesis service manager")
    sub = parser.add_subparsers(dest="command")
    up = sub.add_parser("up", help="install what's missing + start everything (default)")
    up.add_argument("--dev", action="store_true", help="frontend dev mode (hot reload)")
    up.add_argument("--no-tor", action="store_true", help="do not start the safe Tor client")
    up.add_argument("--no-watchdog", action="store_true", help="disable auto-restart supervisor")
    up.add_argument("--no-browser", dest="browser", action="store_false", help="do not open the dashboard")
    up.add_argument("--rebuild", action="store_true", help="force fresh frontend production build")
    up.set_defaults(func=cmd_up, browser=True)
    sub.add_parser("stop", help="stop all background services").set_defaults(func=cmd_stop)
    st = sub.add_parser("status", help="what is running")
    st.set_defaults(func=cmd_status)
    lg = sub.add_parser("logs", help="tail api|web|tor|watchdog logs")
    lg.add_argument("service", choices=["api", "web", "tor", "watchdog", "setup"])
    lg.add_argument("--lines", type=int, default=60)
    lg.set_defaults(func=cmd_logs)
    sub.add_parser("doctor", help="pre-flight diagnostic").set_defaults(func=cmd_doctor)
    wd = sub.add_parser("_watchdog", help=argparse.SUPPRESS)
    wd.set_defaults(func=cmd_watchdog)

    argv = sys.argv[1:]
    subcommands = {"up", "stop", "status", "logs", "doctor", "_watchdog"}
    if not argv or argv[0] not in subcommands:
        argv = ["up", *argv]  # bare flags belong to the default 'up'
    args = parser.parse_args(argv)
    if args.command == "status":
        cmd_status(args)
        return
    args.func(args)


if __name__ == "__main__":
    main()
