# src/ingestion/parsers/ocr_utils.py
import io
from typing import Optional
try:
    from PIL import Image
except Exception:
    raise RuntimeError("Pillow is required for OCR image handling. Install pillow.")
import pytesseract

def ocr_image(image_path: Optional[str] = None, image_bytes: Optional[bytes] = None) -> str:
    """
    Run Tesseract OCR on an image file or image bytes.
    Returns extracted unicode text.
    """
    if not image_path and not image_bytes:
        return ""

    if image_path:
        img = Image.open(image_path)
    else:
        assert image_bytes is not None, "image_bytes must be provided when image_path is not set"
        img = Image.open(io.BytesIO(image_bytes))

    text = pytesseract.image_to_string(img, lang='eng')  # lang can be adjusted
    return text or ""
