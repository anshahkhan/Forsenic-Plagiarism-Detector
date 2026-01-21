from typing import Tuple
import numpy as np
import hashlib
from sklearn.feature_extraction.text import CountVectorizer
import spacy
from sentence_transformers import SentenceTransformer, util

# Load NLP and embedding models once
_nlp = spacy.load("en_core_web_sm")
_sem_model = SentenceTransformer("all-MiniLM-L6-v2")

def lexical_similarity(text1: str, text2: str, n=3) -> float:
    vec = CountVectorizer(analyzer='word', ngram_range=(n, n))
    vec1 = vec.build_analyzer()(text1)
    vec2 = vec.build_analyzer()(text2)
    union_len = len(set(vec1) | set(vec2))
    return len(set(vec1) & set(vec2)) / union_len if union_len > 0 else 0.0

def grammar_similarity(text1: str, text2: str) -> float:
    pos1 = " ".join([token.pos_ for token in _nlp(text1)])
    pos2 = " ".join([token.pos_ for token in _nlp(text2)])
    return lexical_similarity(pos1, pos2, n=3)

def semantic_similarity(text1: str, text2: str) -> float:
    if not text1.strip() or not text2.strip():
        return 0.0

    emb1 = _sem_model.encode(text1, convert_to_tensor=True)
    emb2 = _sem_model.encode(text2, convert_to_tensor=True)

    cosine = util.cos_sim(emb1, emb2).item()
    normalized = (cosine + 1) / 2  # convert [-1,1] → [0,1]
    return normalized


def fingerprint(text: str, k: int = 5) -> set:
    words = text.split()
    hashes = [hashlib.md5(" ".join(words[i:i+k]).encode()).hexdigest()
              for i in range(len(words)-k+1)]
    return set(hashes)

def fingerprint_similarity(text1: str, text2: str, k: int = 5) -> float:
    f1 = fingerprint(text1, k)
    f2 = fingerprint(text2, k)
    union_len = len(f1 | f2)
    return len(f1 & f2) / union_len if union_len > 0 else 0.0

def exact_match_score(target_text: str, candidate_text: str) -> float:
    target_words = set(target_text.split())
    candidate_words = set(candidate_text.split())
    if not target_words:
        return 0.0
    overlap = target_words & candidate_words
    return len(overlap) / len(target_words)

def score_text_pair(text1: str, text2: str) -> Tuple[float, float, float, float]:
    """
    Returns embedding similarity, lexical similarity, combined score, exact_match_score
    """
    lex_sim = lexical_similarity(text1, text2)
    gram_sim = grammar_similarity(text1, text2)
    sem_sim = semantic_similarity(text1, text2)
    fprint_sim = fingerprint_similarity(text1, text2)
    exact_sim = exact_match_score(text1, text2)

    # Configurable weights
    combined = 0.25*lex_sim + 0.15*gram_sim + 0.35*sem_sim + 0.1*fprint_sim + 0.15*exact_sim

    return sem_sim, lex_sim, combined, exact_sim
