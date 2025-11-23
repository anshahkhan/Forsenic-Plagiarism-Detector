# src/similarity_search/evidence_algorithms/exact_matcher.py
import re
from typing import List, Dict, Any
from ..utils import generate_ngrams, char_index_spans, min_token_length

class ExactMatcher:
    """
    Identifies exact n-gram matches (word-level) and strong lexical overlaps.
    """

    def __init__(self, nlp=None, min_ngram=5):
        self.nlp = nlp
        self.min_ngram = min_ngram

    def find_exact_matches(self, original: str, source: str) -> List[Dict[str, Any]]:
        o_tokens = re.findall(r"\w+|\S", original)
        s_tokens = re.findall(r"\w+|\S", source)

        matches = []

        # n-gram search for n in descending order (5 -> 1)
        for n in range(5, self.min_ngram - 1, -1):
            o_ngrams = generate_ngrams(o_tokens, n)
            s_ngrams = generate_ngrams(s_tokens, n)

            s_index = {ngram: idx for idx, (ngram, idx) in enumerate(s_ngrams)}
            for o_ngram, o_idx in o_ngrams:
                if o_ngram in s_index:
                    s_idx = s_index[o_ngram]
                    o_char_span = char_index_spans(original, o_tokens, o_idx, n)
                    s_char_span = char_index_spans(source, s_tokens, s_idx, n)
                    matches.append({
                        "type": "exact_match",
                        "original_text": original[o_char_span[0]:o_char_span[1]],
                        "source_text": source[s_char_span[0]:s_char_span[1]],
                        "match_length": n,
                        "original_span": o_char_span,
                        "source_span": s_char_span,
                        "confidence": 0.95 + 0.01 * (n - self.min_ngram)  # slightly higher for longer n
                    })

        # merge / dedupe by span (caller will consolidate)
        return matches
