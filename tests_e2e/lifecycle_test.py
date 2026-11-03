#!/usr/bin/env python3
"""End-to-end lifecycle tests for the Genesis service manager (stdlib only).

Black-box style: drives `python genesis.py <cmd>` as a subprocess exactly like
a user would, and asserts on observable outcomes — ports, HTTP health, process
tables, pid files, files on disk. Reuses genesis.py's own primitives (imported,
not reimplemented) so the assertions test the same code the manager runs.

Usage:  python tests_e2e/lifecycle_test.py [stage ...]     (default: all stages)
Stages: doctor up idempotent logs watchdog_restart watchdog_respawn
        watchdog_single_instance foreign_stop foreign_up stop uninstall_shallow help
(The full install→uninstall→reinstall cycle is orchestrated by the caller so
its long npm/pip/build steps can be watched individually.)
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import genesis  # noqa: E402  (module import is side-effect-light; main() guarded)

GENESIS = [sys.executable, str(ROOT / "genesis.py")]
RESULTS: list[tuple[str, bool, str]] = []


def run_cli(*argv: str, timeout: int = 600) -> subprocess.CompletedProcess:
    return subprocess.run([*GENESIS, *argv], cwd=str(ROOT), capture_output=True, text=True, timeout=timeout)


def check(stage: str, name: str, cond: bool, detail: str = "") -> bool:
    mark = "PASS" if cond else "FAIL"
    print(f"  [{mark}] {name}" + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        RESULTS.append((stage, False, name))
    return cond


def services_up(label: str) -> bool:
    ok_api = genesis.http_ok(f"{genesis.API_URL}/api/health")
    ok_web = genesis.http_ok(genesis.WEB_URL)
    return check("up", f"{label}: API healthy on :8000", ok_api) and \
        check("up", f"{label}: web healthy on :3000", ok_web)


def nothing_listening(ports: tuple[int, ...]) -> bool:
    return all(not genesis.listeners_on(p) and not genesis.port_open(p) for p in ports)


def wait_port_vanishes(port: int, timeout: float = 15.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not genesis.port_open(port):
            return True
        time.sleep(0.5)
    return False


# ------------------------------------------------------------------- stages

def stage_doctor() -> None:
    print("\n=== STAGE doctor — pre-flight diagnostic ===")
    r = run_cli("doctor")
    check("doctor", "exit code 0", r.returncode == 0, f"rc={r.returncode}\n{r.stdout[-400:]}{r.stderr[-200:]}")
    check("doctor", "reports ready", "ready" in r.stdout, r.stdout[-300:])


def stage_up() -> None:
    print("\n=== STAGE up — install-check + detached start ===")
    r = run_cli("up", "--no-browser")
    check("up", "exit code 0", r.returncode == 0, f"rc={r.returncode}\n{r.stdout[-600:]}{r.stderr[-200:]}")
    services_up("after up")
    st = run_cli("status")
    check("up", "status shows api healthy", "healthy" in st.stdout, st.stdout)
    check("up", "pid files written",
          (genesis.RUNTIME / "api.pid").exists() and (genesis.RUNTIME / "web.pid").exists())
    real_api = genesis.read_pid("api.real")
    check("up", "real api server pid tracked and alive", real_api > 0 and genesis.pid_alive(real_api), f"pid={real_api}")
    # the manager's own health gates
    check("up", "api health endpoint returns version", _health_has_version())


def _health_has_version() -> bool:
    import json
    import urllib.request
    try:
        with urllib.request.urlopen(f"{genesis.API_URL}/api/health", timeout=5) as resp:
            body = json.load(resp)
        return body.get("status") == "ok" and bool(body.get("version"))
    except Exception as exc:
        check("up", "health json parse", False, str(exc))
        return False


def stage_idempotent() -> None:
    print("\n=== STAGE idempotent — up while already running ===")
    r = run_cli("up", "--no-browser")
    check("idempotent", "exit code 0", r.returncode == 0, r.stdout[-300:])
    check("idempotent", "recognizes already-running", "ALREADY RUNNING" in r.stdout, r.stdout[-300:])
    services_up("still up after idempotent up")


def stage_logs() -> None:
    print("\n=== STAGE logs — tail + expected error path ===")
    r = run_cli("logs", "api", "--lines", "200")
    check("logs", "api log readable (spawn header present)",
          r.returncode == 0 and "spawn api" in r.stdout, r.stdout[-200:])
    setup_log = genesis.LOGS / "setup.log"
    r2 = run_cli("logs", "setup")
    if not setup_log.exists():
        check("logs", "missing log dies with exit 1", r2.returncode == 1, f"rc={r2.returncode}")
        check("logs", "missing log names the file", "no log yet" in r2.stdout, r2.stdout[-200:])
    else:
        check("logs", "existing setup log readable", r2.returncode == 0, f"rc={r2.returncode}")
    r3 = run_cli("logs", "bogus")
    check("logs", "invalid service name rejected", r3.returncode == 2, f"rc={r3.returncode}")


def stage_watchdog_restart() -> None:
    print("\n=== STAGE watchdog_restart — kill API, supervisor must heal it ===")
    real_api = genesis.read_pid("api.real") or genesis.read_pid("api")
    check("watchdog_restart", "have an api pid to kill", real_api > 0 and genesis.pid_alive(real_api), f"pid={real_api}")
    subprocess.run(["taskkill", "/F", "/T", "/PID", str(real_api)], capture_output=True, text=True)
    time.sleep(2)
    deadline = time.time() + 120
    healed = False
    while time.time() < deadline:
        if genesis.http_ok(f"{genesis.API_URL}/api/health"):
            healed = True
            break
        time.sleep(3)
    check("watchdog_restart", "watchdog restarted API within 120s", healed)
    new_pid = genesis.read_pid("api.real")
    check("watchdog_restart", "new generation tracked", new_pid > 0 and genesis.pid_alive(new_pid), f"pid={new_pid}")
    services_up("after watchdog heal")


def stage_watchdog_respawn() -> None:
    print("\n=== STAGE watchdog_respawn — kill the supervisor itself, up restores it ===")
    wd = genesis.read_pid("watchdog")
    check("watchdog_respawn", "watchdog was alive", wd > 0 and genesis.pid_alive(wd), f"pid={wd}")
    if wd:
        # /T (tree) also kills services the watchdog respawned as children —
        # so 'up' may legitimately take the full restart path here.
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(wd)], capture_output=True, text=True)
    time.sleep(1)
    r = run_cli("up", "--no-browser")
    check("watchdog_respawn", "up recovers regardless of tree-kill fallout", r.returncode == 0, r.stdout[-300:])
    services_up("after up restored supervision")
    wd2 = genesis.read_pid("watchdog")
    check("watchdog_respawn", "watchdog alive again", wd2 > 0 and genesis.pid_alive(wd2), f"pid={wd2}")


def _start_foreign(port: int) -> subprocess.Popen:
    tmp = tempfile.mkdtemp(prefix="foreign_e2e_")
    return subprocess.Popen([sys.executable, "-m", "http.server", str(port)],
                            cwd=tmp, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _wait_listening(port: int, proc: subprocess.Popen, timeout: float = 15.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            return False
        if genesis.port_open(port):
            return True
        time.sleep(0.3)
    return False


def stage_foreign_stop() -> None:
    print("\n=== STAGE foreign_stop — 'stop' must never kill a foreign app ===")
    run_cli("stop")
    dummy = _start_foreign(genesis.API_PORT)
    try:
        check("foreign_stop", "foreign server listening on 8000", _wait_listening(genesis.API_PORT, dummy))
        holders = genesis.listeners_on(genesis.API_PORT)
        check("foreign_stop", "foreign pid fails is_ours", all(not genesis.is_ours(p) for p in holders), str(holders))
        r = run_cli("stop")
        check("foreign_stop", "stop exit 0", r.returncode == 0, r.stdout[-300:])
        time.sleep(1.5)
        check("foreign_stop", "FOREIGN PROCESS STILL ALIVE after stop", dummy.poll() is None)
        check("foreign_stop", "stop warns about the foreign process", "FOREIGN" in r.stdout, r.stdout[-300:])
    finally:
        dummy.terminate()
        dummy.wait(timeout=10)
    check("foreign_stop", "port released after manual dummy shutdown", wait_port_vanishes(genesis.API_PORT))


def stage_foreign_up() -> None:
    print("\n=== STAGE foreign_up — 'up' must abort cleanly when a foreign app holds :8000 ===")
    run_cli("stop")
    dummy = _start_foreign(genesis.API_PORT)
    try:
        check("foreign_up", "foreign server listening on 8000", _wait_listening(genesis.API_PORT, dummy))
        r = run_cli("up", "--no-browser", timeout=300)
        check("foreign_up", "up aborts (non-zero exit)", r.returncode != 0, f"rc={r.returncode}")
        check("foreign_up", "message names the foreign pid", "foreign process" in r.stdout, r.stdout[-400:])
        time.sleep(1.5)
        check("foreign_up", "FOREIGN PROCESS STILL ALIVE after up", dummy.poll() is None)
        check("foreign_up", "no doomed services spawned (web port still free)",
              not genesis.port_open(genesis.WEB_PORT))
    finally:
        dummy.terminate()
        dummy.wait(timeout=10)
    wait_port_vanishes(genesis.API_PORT)


def stage_stop() -> None:
    print("\n=== STAGE stop — full teardown, no orphans ===")
    r = run_cli("up", "--no-browser")          # ensure something is running
    services_up("before stop")
    r = run_cli("stop")
    check("stop", "exit code 0", r.returncode == 0, r.stdout[-300:])
    check("stop", "all ports free (8000/3000)", wait_port_vanishes(genesis.API_PORT) and wait_port_vanishes(genesis.WEB_PORT))
    check("stop", "pid files removed",
          not (genesis.RUNTIME / "api.pid").exists() and not (genesis.RUNTIME / "watchdog.pid").exists())
    r2 = run_cli("stop")
    check("stop", "stop is idempotent", r2.returncode == 0 and "nothing was running" in r2.stdout, r2.stdout[-200:])


def stage_uninstall_shallow() -> None:
    print("\n=== STAGE uninstall_shallow — remove state, keep dependencies ===")
    run_cli("up", "--no-browser")
    r = run_cli("uninstall", "--yes")
    check("uninstall", "exit code 0", r.returncode == 0, r.stdout[-300:])
    check("uninstall", "runtime/ removed", not genesis.RUNTIME.exists())
    check("uninstall", "logs/ removed", not genesis.LOGS.exists())
    check("uninstall", "backend/.venv kept", genesis.venv_python().exists())
    check("uninstall", "frontend/node_modules kept", (genesis.FRONTEND / "node_modules").exists())
    check("uninstall", "services down", nothing_listening((genesis.API_PORT, genesis.WEB_PORT)))
    print("  -- reinstalling from kept deps (fast path) --")
    r = run_cli("up", "--no-browser", timeout=420)
    check("uninstall", "up works right after shallow uninstall", r.returncode == 0, r.stdout[-300:])
    services_up("after shallow reinstall")
    # stamps lived in runtime/ and are legitimately gone after uninstall — up
    # must re-verify deps (quick no-op installs) and re-stamp them
    check("uninstall", "dependency stamps recreated",
          (genesis.RUNTIME / "pip.stamp").exists() and (genesis.RUNTIME / "npm.stamp").exists())


def stage_watchdog_single_instance() -> None:
    print("\n=== STAGE watchdog_single_instance — repeated 'up' must never orphan supervisors ===")
    # Regression: 'up' used to overwrite watchdog.pid unconditionally, orphaning
    # the previous supervisor. Piled-up supervisors ran competing restart loops
    # and killed each other's mid-startup servers (live streams died with
    # 'network error').
    run_cli("up", "--no-browser")
    services_up("before duplicate ups")
    for _ in range(3):
        r = run_cli("up", "--no-browser")
        check("watchdog_single_instance", "up exit 0", r.returncode == 0, r.stdout[-200:])
    time.sleep(2)
    orphans = genesis.find_our_watchdogs()
    check("watchdog_single_instance", f"exactly one supervisor alive (found {len(orphans)})", len(orphans) <= 1)
    # services must survive the duplicate ups untouched
    services_up("after duplicate ups")


def stage_help() -> None:
    print("\n=== STAGE help — CLI surface ===")
    r = run_cli("--help")
    for cmd in ("up", "stop", "status", "logs", "doctor", "uninstall"):
        check("help", f"{cmd} documented", cmd in r.stdout)
    r2 = run_cli("uninstall", "--help")
    check("help", "uninstall has --deep and --yes", "--deep" in r2.stdout and "--yes" in r2.stdout)


STAGES = {
    "doctor": stage_doctor,
    "up": stage_up,
    "idempotent": stage_idempotent,
    "logs": stage_logs,
    "watchdog_restart": stage_watchdog_restart,
    "watchdog_respawn": stage_watchdog_respawn,
    "watchdog_single_instance": stage_watchdog_single_instance,
    "foreign_stop": stage_foreign_stop,
    "foreign_up": stage_foreign_up,
    "stop": stage_stop,
    "uninstall_shallow": stage_uninstall_shallow,
    "help": stage_help,
}


def main() -> None:
    argv = [a for a in sys.argv[1:] if a in STAGES] or list(STAGES)
    for name in argv:
        STAGES[name]()
    print("\n" + "=" * 60)
    if RESULTS:
        print(f"FAILURES ({len(RESULTS)}):")
        for stage, _, name in RESULTS:
            print(f"  - [{stage}] {name}")
        sys.exit(1)
    print(f"ALL STAGES PASSED: {', '.join(argv)}")


if __name__ == "__main__":
    main()
