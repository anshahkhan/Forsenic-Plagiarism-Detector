# src/similarity_search/evidence_algorithms/idea_matcher.py
from typing import Dict, Any
import numpy as np
from ..utils import block_embedding, sequence_order_similarity

class IdeaMatcher:
    """
    Detects structural / idea similarity: order, topic progression and block-level embeddings.
    """

    def __init__(self, embedder=None):
        self.embedder = embedder

    def find_idea_matches(self, original: str, source: str) -> Dict[str, Any]:
        if not self.embedder:
            # fallback simple heuristic
            score = sequence_order_similarity(original, source)
            return {"type": "idea_similarity", "score": float(score), "explanation": "order-based heuristic"}
        o_emb = block_embedding(self.embedder, original)
        s_emb = block_embedding(self.embedder, source)
        sim = float(np.dot(o_emb, s_emb) / (np.linalg.norm(o_emb) * np.linalg.norm(s_emb) + 1e-9))
        explanation = "block embedding cosine similarity"
        return {"type": "idea_similarity", "score": sim, "explanation": explanation}
