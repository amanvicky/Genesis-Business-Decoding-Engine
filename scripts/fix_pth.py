"""Enable site-packages in an embeddable Python distribution.

The python.org embeddable zip ships a `pythonXY._pth` file that locks down
sys.path (pip cannot install into it). Uncommenting its `import site` line is
the documented recipe. Kept as a tiny script so the fix is testable and runs
UNDER the embeddable interpreter itself (core stdlib works before site is
enabled; only site-packages are gated by the _pth file).
"""
import pathlib
import re
import sys


def fix_dir(directory: pathlib.Path) -> int:
    """Uncomment `import site` in every python*._pth. Returns files changed."""
    changed = 0
    for pth in sorted(pathlib.Path(directory).glob("python*._pth")):
        text = pth.read_text(encoding="utf-8")
        fixed = re.sub(r"^#\s*(import site)\s*$", r"\1", text, flags=re.MULTILINE)
        if fixed != text:
            pth.write_text(fixed, encoding="utf-8")
            print(f"[OK] enabled site-packages: {pth.name}")
            changed += 1
    return changed


if __name__ == "__main__":
    target = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(".")
    if not target.is_dir():
        print(f"[X] not a directory: {target}")
        sys.exit(1)
    n = fix_dir(target)
    if n == 0:
        print("[*] no ._pth files needed fixing")
