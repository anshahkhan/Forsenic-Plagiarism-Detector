import re
from typing import Dict
from sentence_transformers import SentenceTransformer
import numpy as np

_model = SentenceTransformer("all-MiniLM-L6-v2")

def clean_text(text: str) -> str:
    text = re.sub(r"\[[^\]]+\]", "", text)
    text = re.sub(r"\([^\)]*et al\.[^\)]*\)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\([^\)]*\d{4}[^\)]*\)", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def select_key_sentences(text: str, max_sentences: int = 3, max_chars: int = 200) -> str:
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
    if not sentences:
        return ""
    sentence_embeddings = _model.encode(sentences)
    block_embedding = _model.encode([text])[0]
    scores = np.dot(sentence_embeddings, block_embedding) / (
        np.linalg.norm(sentence_embeddings, axis=1) * np.linalg.norm(block_embedding)
    )
    top_idx = np.argsort(scores)[-max_sentences:]
    top_idx = sorted(top_idx)
    selected = [sentences[i] for i in top_idx]
    query_text = " ".join(selected)
    if len(query_text) > max_chars:
        query_text = query_text[:max_chars].rsplit(" ", 1)[0]
    return query_text

def generate_query_for_block(block: Dict) -> Dict:
    """
    Returns dict with 'query' and 'key_sentences'.
    Query instructs LLM to prioritize authoritative sources, but not be restricted to them.
    """
    text = block.get("text", "")
    if not text.strip():
        return {
            "query": (
                "Find authoritative web sources, articles, or publications, "
                "preferably from sources like Google, BBC, IEEE, Medium, Google News, Google Scholar, "
                "but other relevant sources are also acceptable, that discuss: "
            ),
            "key_sentences": ""
        }

    key_sentences = select_key_sentences(clean_text(text))
    
    query = (
        "Find authoritative web sources, articles, or publications, "
        "preferably from sources like Google, BBC, IEEE, Medium, Google News, Google Scholar, "
        f"but other relevant sources are also acceptable, that discuss: {key_sentences}"
    )

    return {"query": query, "key_sentences": key_sentences}


