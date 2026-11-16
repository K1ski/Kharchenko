from pathlib import Path

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
