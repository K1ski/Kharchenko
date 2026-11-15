from pathlib import Path

project = Path("HedgeHelper_v0.1.0")
source_file = project / "hedge_helper" / "ocr_engine.py"
source = source_file.read_text(encoding="utf-8")

if "import sys\n" not in source:
    marker = "import shutil\n"
    if marker not in source:
        raise SystemExit("Cannot patch OCR imports: import shutil not found")
    source = source.replace(marker, "import os\nimport shutil\nimport sys\n", 1)

needle = (
    '        self.languages = languages\n'
    '        cmd = str(Path(tesseract_cmd).expanduser()) if tesseract_cmd else None\n'
)
replacement = (
    '        self.languages = languages\n'
    '        cmd = str(Path(tesseract_cmd).expanduser()) if tesseract_cmd else None\n'
    '        if not cmd:\n'
    '            bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))\n'
    '            bundled_tesseract = bundle_root / "tesseract_runtime" / "tesseract.exe"\n'
    '            if bundled_tesseract.is_file():\n'
    '                cmd = str(bundled_tesseract)\n'
    '                os.environ["TESSDATA_PREFIX"] = str(bundled_tesseract.parent / "tessdata")\n'
)
if "bundled_tesseract = bundle_root / \"tesseract_runtime\"" not in source:
    if needle not in source:
        raise SystemExit("Cannot patch OCR initialization: expected lines not found")
    source = source.replace(needle, replacement, 1)

source_file.write_text(source, encoding="utf-8", newline="\n")
print("Patched OCR engine: bundled Tesseract is auto-detected.")
