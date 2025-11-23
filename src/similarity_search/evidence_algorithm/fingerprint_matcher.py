# src/similarity_search/evidence_algorithms/fingerprint_matcher.py
"""
Winnowing-style fingerprinting: k-gram hashing with sliding window (k=25 characters default).
"""

import hashlib
from typing import List, Dict, Any
from collections import defaultdict

def rolling_hash(s: str):
    return hashlib.blake2b(s.encode("utf8"), digest_size=6).hexdigest()

class FingerprintMatcher:
    def __init__(self, k=25, window=4):
        self.k = k
        self.window = window

    def _fingerprints(self, text: str) -> List[str]:
        fp = []
        for i in range(max(0, len(text) - self.k + 1)):
            gram = text[i:i + self.k]
            fp.append(rolling_hash(gram))
        # simple winnowing: pick every `window`-th fingerprint (not production winnowing but fast)
        return [fp[i] for i in range(0, len(fp), max(1, self.window))]

    def find_fingerprint_matches(self, original: str, source: str) -> Dict[str, Any]:
        o_fp = set(self._fingerprints(original))
        s_fp = set(self._fingerprints(source))
        matching = list(o_fp.intersection(s_fp))
        coverage = (len(matching) / max(1, len(o_fp))) * 100
        return {
            "type": "fingerprint_match",
            "matching_hashes": matching,
            "coverage_percent": coverage
        }
