# src/ingestion/parsers/pdf_parser.py
import os
import uuid
import tempfile
from typing import Dict, List, Any
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LAParams, LTImage
from ..utils import normalize_metadata, detect_language, section_splitter
from .ocr_utils import ocr_image
from pdf2image import convert_from_path
import logging

# Configure logging for debugging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def _extract_images_from_page(page_layout, out_dir: str, page_number: int) -> List[Dict[str, Any]]:
    images_meta: List[Dict[str, Any]] = []

    for obj_index, obj in enumerate(page_layout):
        if isinstance(obj, LTImage):
            try:
                image_bytes = obj.stream.get_rawdata()
                if not image_bytes:
                    continue
                filename = f"img_{uuid.uuid4().hex}_{page_number+1}_{obj_index}.png"
                path = os.path.join(out_dir, filename)
                with open(path, "wb") as f:
                    f.write(image_bytes)
                images_meta.append({"page": page_number + 1, "path": path})
            except Exception as e:
                logging.warning(f"Failed to extract image on page {page_number+1}: {e}")
    return images_meta


def parse_pdf(path: str, ocr_if_no_text: bool = True) -> Dict[str, Any]:
    """
    Parse a PDF using pdfminer.six + optional OCR fallback.
    Returns dict with {doc_id, sections, metadata, raw_text, images}.
    """
    if not os.path.exists(path):
        logging.error(f"PDF file not found: {path}")
        return {}

    doc_id = uuid.uuid4().hex
    pages_text = []
    out_images = []
    metadata = {"file_type": "pdf"}
    empty_pages_idx = []

    # Extract text per page
    laparams = LAParams()
    for page_number, page_layout in enumerate(extract_pages(path, laparams=laparams)):
        page_text = ""
        try:
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    page_text += element.get_text()
            page_text = page_text.strip()
        except Exception as e:
            logging.warning(f"Text extraction failed on page {page_number+1}: {e}")
            page_text = ""

        if not page_text:
            empty_pages_idx.append(page_number)
            pages_text.append("")
        else:
            pages_text.append(page_text)

        # Attempt image extraction
        try:
            tmpdir = tempfile.mkdtemp(prefix="df_imgs_")
            imgs = _extract_images_from_page(page_layout, tmpdir, page_number)
            if imgs:
                out_images.extend(imgs)
        except Exception as e:
            logging.warning(f"Image extraction failed on page {page_number+1}: {e}")

    # OCR fallback for empty pages
    if ocr_if_no_text and empty_pages_idx:
        logging.info(f"Running OCR on {len(empty_pages_idx)} empty pages")
        try:
            pdf_images = convert_from_path(path, dpi=300)
        except Exception as e:
            logging.error(f"Failed to convert PDF to images for OCR: {e}")
            pdf_images = []

        for idx in empty_pages_idx:
            if idx >= len(pdf_images):
                continue
            img = pdf_images[idx]
            try:
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_img:
                    img.save(tmp_img.name, format="PNG")
                    ocr_text = ocr_image(image_bytes=open(tmp_img.name, "rb").read())
                    pages_text[idx] = ocr_text
                    out_images.append({"page": idx + 1, "path": tmp_img.name})
            except Exception as e:
                logging.warning(f"OCR failed for page {idx+1}: {e}")

    raw_text = "\n\n".join([p for p in pages_text if p])

    # Section splitting
    sections = section_splitter(raw_text, pages_text)

    # Language detection
    metadata["language"] = detect_language(raw_text)
    metadata: Dict[str, Any] = {"file_type": "pdf"}
    metadata["num_pages"] = len(pages_text)


    return {
        "doc_id": doc_id,
        "sections": sections,
        "metadata": metadata,
        "raw_text": raw_text,
        "images": out_images,
    }
