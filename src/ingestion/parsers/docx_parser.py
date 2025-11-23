# src/ingestion/parsers/docx_parser.py
from typing import Dict, Any, List
import uuid
from docx import Document
from ..utils import normalize_metadata, detect_language, section_splitter

def parse_docx(path: str) -> Dict[str, Any]:
    doc_id = uuid.uuid4().hex
    doc = Document(path)

    paragraphs = []
    headings = []
    for p in doc.paragraphs:
        text = p.text.strip()
        style_name = p.style.name if p.style is not None else ""
        paragraphs.append(text)
        if style_name.lower().startswith("heading") or text.isupper():
            headings.append(text)

    raw_text = "\n\n".join([p for p in paragraphs if p])

    metadata = {
        "file_type": "docx",
        "num_pages": None,
        "title": None,
        "author": None,
    }

    # Safe extraction and conversion of core properties
    try:
        core = doc.core_properties
        created = getattr(core, "created", None)
        modified = getattr(core, "modified", None)

        # Convert datetime to ISO string if exists
        created_str = created.isoformat() if created else None
        modified_str = modified.isoformat() if modified else None

        metadata = {**metadata, **normalize_metadata({
            "title": core.title,
            "author": core.author,
            "created": created_str,
            "modified": modified_str,
        })}
    except Exception:
        pass

    sections = section_splitter(raw_text, [raw_text])
    metadata["language"] = detect_language(raw_text)

    return {
        "doc_id": doc_id,
        "sections": sections,
        "metadata": metadata,
        "raw_text": raw_text,
        "images": []
    }