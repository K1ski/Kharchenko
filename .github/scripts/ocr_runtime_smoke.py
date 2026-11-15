from hedge_helper.ocr_engine import OcrEngine

engine = OcrEngine()
print(f"Frozen OCR smoke test passed: Tesseract {engine.version}; languages {engine.languages}")
