# src/similarity_search/perplexity_client.py
import requests
from typing import List, Dict
from . import configs
import time
import logging

logger = logging.getLogger(__name__)

HEADERS = {
    "Authorization": f"Bearer {configs.PERPLEXITY_API_KEY}",
    "Content-Type": "application/json"
}

def call_perplexity(query: str, top_k: int = 5) -> List[Dict]:
    """
    Calls Perplexity LLM and returns a list of candidates with:
    title, url, snippet, score (confidence 0.0–1.0)
    """
    if not configs.PERPLEXITY_API_KEY:
        raise RuntimeError("PERPLEXITY_API_KEY missing in .env")

    payload = {
        "model": "sonar",
        "query": query,
        "top_k": top_k
    }

    attempt = 0
    while attempt < getattr(configs, "MAX_RETRIES", 3):
        try:
            resp = requests.post(
                getattr(configs, "PERPLEXITY_API_URL"),
                headers=HEADERS,
                json=payload,
                timeout=getattr(configs, "REQUEST_TIMEOUT", 10)
            )

            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                cleaned = []
                for r in results:
                    # Ensure score is always a float between 0–1
                    raw_score = r.get("score")
                    if raw_score is None:
                        raw_score = 1.0  # default high confidence if missing
                    else:
                        try:
                            raw_score = float(raw_score)
                        except Exception:
                            raw_score = 1.0

                    cleaned.append({
                        "title": r.get("title", "Untitled"),
                        "url": r.get("url"),
                        "snippet": r.get("snippet", ""),
                        "score": raw_score
                    })
                return cleaned

            else:
                logger.warning(f"Perplexity returned {resp.status_code}: {resp.text}")
                attempt += 1
                time.sleep(1 + attempt)

        except requests.RequestException as e:
            logger.warning(f"Perplexity request failed: {e}")
            attempt += 1
            time.sleep(1 + attempt)

    logger.error("Perplexity API failed after %d attempts", attempt)
    return []
