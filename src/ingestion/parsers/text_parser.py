# src/ingestion/parsers/text_parser.py
from typing import Dict, Any, List
import uuid
from ..utils import normalize_metadata, detect_language, section_splitter
import os
from datetime import datetime

UPLOAD_DIR = os.environ.get("DF_UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def parse_text_string(text: str) -> Dict[str, Any]:
    """
    Parse a plain text string into normalized JSON and save as a .txt file
    """
    doc_id = uuid.uuid4().hex
    raw_text = text.strip()

    # Save the text as a .txt file
    file_path = os.path.join(UPLOAD_DIR, f"{doc_id}.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(raw_text)

    sections = section_splitter(raw_text, [raw_text])

    metadata = {
        "file_type": "plain_text",
        "num_pages": None,
        "language": detect_language(raw_text),
        "file_path": file_path,  # optional: store path for reference
    }

    return {
        "doc_id": doc_id,
        "sections": sections,
        "metadata": metadata,
        "raw_text": raw_text,
        "images": [],
        "file_path": file_path,  # include file path for downstream use
    }

def parse_text_file(path: str) -> Dict[str, Any]:
    """
    Parse a plain text file into normalized JSON.
    """
    doc_id = uuid.uuid4().hex

    with open(path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    # Simple metadata
    metadata = {
        "file_type": "txt",
        "num_pages": None,  # Not applicable
        "title": os.path.basename(path),
        "author": None,
        "created": None,
        "modified": None,
        "language": detect_language(raw_text)
    }

    sections = section_splitter(raw_text, [raw_text])

    return {
        "doc_id": doc_id,
        "sections": sections,
        "metadata": metadata,
        "raw_text": raw_text,
        "images": []
    }
