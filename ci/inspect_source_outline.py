from pathlib import Path
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
project = Path("HedgeHelper_v0.1.0")
if not project.is_dir():
    raise SystemExit("Restored project directory is missing")

print("=== HEDGE HELPER SOURCE OUTLINE ===")
for path in sorted(project.rglob("*.py")):
    if any(part in {".venv", "__pycache__", ".pytest_cache"} for part in path.parts):
        continue
    source = path.read_text(encoding="utf-8", errors="replace")
    lines = source.splitlines()
    print(f"\n--- FILE {path.as_posix()} ({len(lines)} lines, {len(source)} chars) ---")
    for number, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith(("class ", "def ", "async def ", "from ", "import ")) or stripped.startswith("@"):
            print(f"{number}: {stripped[:220]}")
print("=== END SOURCE OUTLINE ===")

if "--dump" in sys.argv:
    ranges = {
        "hedge_helper/calculator.py": [(1, 1000)],
        "hedge_helper/models.py": [(1, 1000)],
        "hedge_helper/capture.py": [(1, 1000)],
        "hedge_helper/ocr_engine.py": [(1, 1000)],
        "hedge_helper/monitor.py": [(1, 1000)],
        "hedge_helper/signal_parser.py": [(1, 1000)],
        "hedge_helper/ui.py": [(1, 365), (415, 637)],
    }
    print("\n=== SELECTED SOURCE DUMP ===")
    for relative, spans in ranges.items():
        path = project / relative
        if not path.is_file():
            continue
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        for first, last in spans:
            print(f"\n--- BEGIN {relative}:{first}-{min(last, len(lines))} ---")
            for number in range(first, min(last, len(lines)) + 1):
                print(f"{number:04d}: {lines[number - 1]}")
            print(f"--- END {relative}:{first}-{min(last, len(lines))} ---")
    print("=== END SELECTED SOURCE DUMP ===")
