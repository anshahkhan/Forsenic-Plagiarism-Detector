# src/similarity_search/google_client.py
import requests
import logging
from typing import List, Dict, Optional
from . import configs

logger = logging.getLogger(__name__)

def search_google(query: str, top_k: int = 5) -> List[Dict]:
    """
    Uses Google Custom Search JSON API (requires CSE ID + API key).
    If not configured, returns empty list.
    Each result dict: {title, url, snippet, source_score}
    """
    if not getattr(configs, "GOOGLE_API_KEY", None) or not getattr(configs, "GOOGLE_CSE_ID", None):
        logger.debug("Google CSE not configured")
        return []

    params = {
        "key": configs.GOOGLE_API_KEY,
        "cx": configs.GOOGLE_CSE_ID,
        "q": query,
        "num": min(10, top_k)
    }
    try:
        resp = requests.get("https://www.googleapis.com/customsearch/v1", params=params, timeout=configs.REQUEST_TIMEOUT)
        if resp.status_code != 200:
            logger.warning("Google CSE returned %s: %s", resp.status_code, resp.text)
            return []
        data = resp.json()
        items = data.get("items", [])[:top_k]
        cleaned = []
        for it in items:
            cleaned.append({
                "title": it.get("title"),
                "url": it.get("link"),
                "snippet": it.get("snippet"),
                "score": None
            })
        return cleaned
    except Exception as e:
        logger.warning("Google CSE failed: %s", e)
        return []

def search_google_advanced(
    all_words: Optional[str] = None,
    important_words: Optional[str] = None,
    exact_phrase: Optional[str] = None,
    any_words: Optional[str] = None,
    exclude_words: Optional[str] = None,
    number_range: Optional[str] = None,
    top_k: int = 5
) -> List[Dict]:
    """
    Advanced Google search using CSE API with operators to mimic Google Advanced Search.
    """
    if not getattr(configs, "GOOGLE_API_KEY", None) or not getattr(configs, "GOOGLE_CSE_ID", None):
        logger.debug("Google CSE not configured")
        return []

    # Build query string
    query_parts = []

    if all_words:
        query_parts.append(all_words)
    if important_words:
        query_parts.append(important_words)
    if exact_phrase:
        query_parts.append(f'"{exact_phrase}"')  # wrap in quotes
    if any_words:
        query_parts.append("(" + " OR ".join(any_words.split()) + ")")
    if exclude_words:
        query_parts.append(" ".join([f"-{w}" if not w.startswith('-') else w for w in exclude_words.split()]))
    if number_range:
        query_parts.append(number_range)

    query = " ".join(query_parts)

    params = {
        "key": configs.GOOGLE_API_KEY,
        "cx": configs.GOOGLE_CSE_ID,
        "q": query,
        "num": min(10, top_k)
    }

    try:
        resp = requests.get("https://www.googleapis.com/customsearch/v1", params=params, timeout=configs.REQUEST_TIMEOUT)
        if resp.status_code != 200:
            logger.warning("Google CSE returned %s: %s", resp.status_code, resp.text)
            return []
        data = resp.json()
        items = data.get("items", [])[:top_k]
        return [{
            "title": it.get("title"),
            "url": it.get("link"),
            "snippet": it.get("snippet"),
            "score": None
        } for it in items]

    except Exception as e:
        logger.warning("Google CSE failed: %s", e)
        return []


def search_bing(query: str, top_k: int = 5) -> List[Dict]:
    """
    Optional Bing Web Search fallback. Requires BING_API_KEY in configs.
    """
    if not getattr(configs, "BING_API_KEY", None):
        return []
    try:
        headers = {"Ocp-Apim-Subscription-Key": configs.BING_API_KEY}
        params = {"q": query, "count": top_k}
        resp = requests.get("https://api.bing.microsoft.com/v7.0/search", headers=headers, params=params, timeout=configs.REQUEST_TIMEOUT)
        if resp.status_code != 200:
            logger.warning("Bing returned %s", resp.status_code)
            return []
        data = resp.json()
        web = data.get("webPages", {}).get("value", [])[:top_k]
        cleaned = []
        for it in web:
            cleaned.append({
                "title": it.get("name"),
                "url": it.get("url"),
                "snippet": it.get("snippet"),
                "score": None
            })
        return cleaned
    except Exception as e:
        logger.warning("Bing search failed: %s", e)
        return []
