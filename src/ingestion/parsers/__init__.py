# src/ingestion/parsers/__init__.py
from .pdf_parser import parse_pdf
from .docx_parser import parse_docx
from .html_parser import parse_html
from .ocr_utils import ocr_image

__all__ = ["parse_pdf", "parse_docx", "parse_html", "ocr_image"]
