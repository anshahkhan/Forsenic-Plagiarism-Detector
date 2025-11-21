# src/ingestion/utils.py
import re
from typing import List, Dict, Any
from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0

def normalize_file_path(path: str) -> str:
    return path

def normalize_metadata(raw_meta: Dict[str, Any]) -> Dict[str, Any]:
    # Normalize common PDF / doc metadata dictionaries to a consistent schema
    meta = {}
    meta["title"] = raw_meta.get("title") or raw_meta.get("Title")
    meta["author"] = raw_meta.get("author") or raw_meta.get("Author")
    # created/modified might be in different keys
    meta["created"] = raw_meta.get("creationDate") or raw_meta.get("created") or raw_meta.get("CreationDate")
    meta["modified"] = raw_meta.get("modDate") or raw_meta.get("modified")
    return meta

def detect_language(text: str) -> str:
    if not text or not text.strip():
        return "und"
    try:
        lang = detect(text)
        return lang
    except Exception:
        return "und"

# Simple rule-based section splitter
SECTION_HEADERS = [
    r"^\s*abstract\s*$",
    r"^\s*introduction\s*$",
    r"^\s*background\s*$",
    r"^\s*methods\s*$",
    r"^\s*methodology\s*$",
    r"^\s*results\s*$",
    r"^\s*discussion\s*$",
    r"^\s*conclusions?\s*$",
    r"^\s*references\s*$",
    r"^\s*acknowledg(e)?ments?\s*$"
]
SECTION_HEADERS_RE = re.compile("|".join(f"({h})" for h in SECTION_HEADERS), flags=re.I | re.M)

def section_splitter(full_text: str, pages_text: List[str]) -> List[Dict[str, Any]]:
    """
    Very small heuristic splitter: finds headings that match SECTION_HEADERS_RE and cuts text.
    Returns list of {name, text, start_page, end_page}.
    """
    if not full_text:
        return []

    lines = full_text.splitlines()
    # Find indices of lines that match headers
    header_positions = []
    for i, line in enumerate(lines):
        if SECTION_HEADERS_RE.match(line.strip()):
            header_positions.append((i, line.strip()))

    if not header_positions:
        # fallback: single section "body"
        return [{"name": "body", "text": full_text.strip(), "start_page": 1, "end_page": len(pages_text)}]

    sections = []
    for idx, (line_idx, header) in enumerate(header_positions):
        start_line = line_idx + 1
        end_line = header_positions[idx + 1][0] if idx + 1 < len(header_positions) else len(lines)
        section_text = "\n".join(lines[start_line:end_line]).strip()
        name = header.strip()
        sections.append({
            "name": name,
            "text": section_text,
            "start_page": 1,
            "end_page": len(pages_text)
        })
    return sections
