import logging
import requests
import re
from typing import Optional
from . import configs
from src.ingestion.utils import split_sentences
logger = logging.getLogger(__name__)

try:
    import trafilatura
    _HAS_TRAFILATURA = True
except ImportError:
    _HAS_TRAFILATURA = False

try:
    from newspaper import Article
    _HAS_NEWSPAPER = True
except ImportError:
    _HAS_NEWSPAPER = False

try:
    import pdfplumber
    _HAS_PDFPLUMBER = True
except ImportError:
    _HAS_PDFPLUMBER = False

_FETCH_CACHE = {}
def fetch_full_text(url: str, timeout: Optional[int] = None) -> Optional[str]:
    """
    Fetch text from URL, attempt multiple strategies (trafilatura, newspaper, PDF),
    then split into sentences for better exact match detection.
    """
    timeout = timeout or getattr(configs, "REQUEST_TIMEOUT", 10)
    if not url:
        return None

    if url in _FETCH_CACHE:
        return _FETCH_CACHE[url]

    text = None
    headers = {"User-Agent": getattr(configs, "HTTP_USER_AGENT", "Mozilla/5.0")}

    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        if r.status_code != 200:
            return None
        html_content = r.text

        # 1️⃣ Trafilatura
        if _HAS_TRAFILATURA:
            extracted = trafilatura.extract(html_content, url=url)
            if extracted:
                text = extracted.strip()

        # 2️⃣ Newspaper fallback
        if not text and _HAS_NEWSPAPER:
            article = Article(url)
            article.download()
            article.parse()
            if article.text:
                text = article.text.strip()

        # 3️⃣ PDF fallback
        if not text and url.lower().endswith(".pdf") and _HAS_PDFPLUMBER:
            import io
            r_pdf = requests.get(url, headers=headers, timeout=timeout)
            if r_pdf.status_code == 200:
                pdf_file = io.BytesIO(r_pdf.content)
                text_pages = []
                with pdfplumber.open(pdf_file) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_pages.append(page_text)
                text = "\n".join(text_pages).strip()

        # 4️⃣ Basic HTML fallback
        if not text:
            html = re.sub(r"(?is)<(script|style).*?>.*?(</\1>)", "", r.text)
            html = re.sub(r"(?is)<.*?>", " ", html)
            text = re.sub(r"\s+", " ", html).strip()

        # 5️⃣ Sentence splitting for expansion
        if text:
            sentences = split_sentences(text)  # or use spacy nlp to split
            expanded_text = " ".join([s.strip() for s in sentences if s.strip()])
            text = expanded_text[:getattr(configs, "MAX_FETCHED_TEXT_CHARS", 20000)]

    except Exception as e:
        logger.warning("Failed to fetch/parse %s: %s", url, e)
        text = None

    _FETCH_CACHE[url] = text
    return text
