# src/similarity_search/evidence_algorithms/paraphrase_matcher.py
from typing import List, Dict, Any, Tuple
import numpy as np
from ..utils import split_sentences, top_k_sentence_pairs, cosine_sim

class ParaphraseMatcher:
    """
    Uses embedding similarity + POS pattern heuristics to detect paraphrase pairs.
    Requires an embedder that can encode sentences.
    """

    def __init__(self, nlp=None, embedder=None, sim_threshold=0.75):
        self.nlp = nlp
        self.embedder = embedder
        self.sim_threshold = sim_threshold

    def find_paraphrase_matches(self, original: str, source: str) -> List[Dict[str, Any]]:
        orig_sents = split_sentences(original)
        src_sents = split_sentences(source)
        if not self.embedder:
            # fallback to token-based heuristic if embedder missing
            return self._heuristic_paraphrase(orig_sents, src_sents)

        o_emb = self.embedder.encode(orig_sents, normalize=True)
        s_emb = self.embedder.encode(src_sents, normalize=True)

        pairs = top_k_sentence_pairs(o_emb, s_emb, top_k=3)
        results = []
        for i, j, score in pairs:
            if score >= self.sim_threshold:
                results.append({
                    "type": "paraphrased_match",
                    "original_sentence": orig_sents[i],
                    "source_sentence": src_sents[j],
                    "semantic_similarity": float(score),
                    "original_index": i,
                    "source_index": j
                })
        return results

    def _heuristic_paraphrase(self, orig_sents, src_sents):
        # cheap fallback
        res = []
        for i, o in enumerate(orig_sents):
            for j, s in enumerate(src_sents):
                if len(o) > 40 and o.split()[:3] == s.split()[:3]:
                    res.append({
                        "type": "paraphrased_match",
                        "original_sentence": o,
                        "source_sentence": s,
                        "semantic_similarity": 0.6,
                        "original_index": i,
                        "source_index": j
                    })
        return res
