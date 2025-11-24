import logging
import requests
import re
from typing import Optional
from . import configs
from src.ingestion.utils import split_sentences

logger = logging.getLogger(__name__)

# Optional libraries
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


# Cache to avoid refetching the same URL
_FETCH_CACHE = {}


def fetch_full_text(url: str, timeout: Optional[int] = None) -> Optional[str]:
    """
    Fetch text from a URL using multiple scraping strategies.
    Respects ALLOW_PDF_SCRAPING flag from configs.
    """
    timeout = timeout or getattr(configs, "REQUEST_TIMEOUT", 10)
    if not url:
        return None

    # Cache hit
    if url in _FETCH_CACHE:
        return _FETCH_CACHE[url]

    # Detect PDF
    is_pdf = url.lower().endswith(".pdf")

    # ============================================================
    # 0️⃣ PDF scraping disabled → immediately skip
    # ============================================================
    if is_pdf and not configs.ALLOW_PDF_SCRAPING:
        logger.info(f"Skipping PDF scraping for {url} (ALLOW_PDF_SCRAPING = False)")
        _FETCH_CACHE[url] = None
        return None

    text = None
    headers = {"User-Agent": getattr(configs, "HTTP_USER_AGENT", "Mozilla/5.0")}

    try:
        # Fetch HTML or PDF content
        r = requests.get(url, headers=headers, timeout=timeout)
        if r.status_code != 200:
            return None

        html_content = r.text

        # ============================================================
        # 1️⃣ Trafilatura extraction
        # ============================================================
        if _HAS_TRAFILATURA:
            extracted = trafilatura.extract(html_content, url=url)
            if extracted:
                text = extracted.strip()

        # ============================================================
        # 2️⃣ Newspaper3k fallback
        # ============================================================
        if not text and _HAS_NEWSPAPER and not is_pdf:
            try:
                article = Article(url)
                article.download()
                article.parse()
                if article.text:
                    text = article.text.strip()
            except Exception:
                pass

        # ============================================================
        # 3️⃣ PDF extraction (only if allowed)
        # ============================================================
        if (
            not text and
            is_pdf and
            configs.ALLOW_PDF_SCRAPING and
            _HAS_PDFPLUMBER
        ):
            import io
            r_pdf = requests.get(url, headers=headers, timeout=timeout)

            if r_pdf.status_code == 200:
                pdf_file = io.BytesIO(r_pdf.content)
                text_pages = []
                try:
                    with pdfplumber.open(pdf_file) as pdf:
                        for page in pdf.pages:
                            page_text = page.extract_text()
                            if page_text:
                                text_pages.append(page_text)
                    text = "\n".join(text_pages).strip()
                except Exception as pdf_err:
                    logger.warning(f"PDF parsing failed for {url}: {pdf_err}")

        # ============================================================
        # 4️⃣ Very simple HTML strip fallback
        # ============================================================
        if not text:
            clean_html = re.sub(r"(?is)<(script|style).*?>.*?(</\1>)", "", html_content)
            clean_html = re.sub(r"(?is)<.*?>", " ", clean_html)
            clean_html = re.sub(r"\s+", " ", clean_html)
            text = clean_html.strip()

        # ============================================================
        # 5️⃣ Sentence splitting
        # ============================================================
        if text:
            sentences = split_sentences(text)
            text = " ".join([s.strip() for s in sentences if s.strip()])

            # Truncate if too large
            max_chars = getattr(configs, "MAX_FETCHED_TEXT_CHARS", 20000)
            text = text[:max_chars]

    except Exception as e:
        logger.warning("Failed to fetch/parse %s: %s", url, e)
        text = None

    _FETCH_CACHE[url] = text
    return text
