# src/ingestion/parsers/html_parser.py
from typing import Dict, Any, List
import uuid
from bs4 import BeautifulSoup
from ..utils import normalize_metadata, detect_language, section_splitter

def parse_html(path: str) -> Dict[str, Any]:
    """
    Parse an HTML file (path) saved locally into normalized JSON.
    """
    doc_id = uuid.uuid4().hex
    with open(path, "rb") as f:
        content = f.read()
    soup = BeautifulSoup(content.decode("utf-8"), "html.parser")

    # Remove scripts & style
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    # Extract headings and paragraphs
    texts = []
    for el in soup.find_all(["h1", "h2", "h3", "h4", "h5", "p"]):
        t = el.get_text(separator=" ", strip=True)
        if t:
            texts.append(t)

    raw_text = "\n\n".join(texts)
    metadata = {
        "file_type": "html",
        "title": soup.title.string if soup.title else None,
        "num_pages": 1
    }
    sections = section_splitter(raw_text, [raw_text])
    metadata["language"] = detect_language(raw_text)
    return {"doc_id": doc_id, "sections": sections, "metadata": metadata, "raw_text": raw_text, "images": []}
