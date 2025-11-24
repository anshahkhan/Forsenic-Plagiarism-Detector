import re
from typing import List, Dict, Any
from ahocorasick import Automaton
from src.ingestion.utils import split_sentences, normalize_text, get_ngrams
from src.similarity_search.web_fetcher import fetch_full_text
from src.similarity_search import configs
from src.similarity_search.similarity_engine import semantic_similarity
import spacy

# -----------------------------
# NLP / Meaningfulness
# -----------------------------
nlp = spacy.load("en_core_web_sm")

def is_meaningful_sentence(text: str) -> bool:
    """
    Returns True only if sentence is meaningful:
    - At least 5–6 words
    - Contains a verb
    - Not a stopword fragment
    """
    text = text.strip()
    words = text.split()

    if len(words) < 5:  # prevents "to prevent"
        return False

    # Must contain a verb (basic heuristic)
    verb_markers = ["is", "are", "was", "were", "be", "can", "has", "have", "does", "did", "shall", "will"]
    if not any(v in text.lower() for v in verb_markers):
        return False

    return True


# -----------------------------
# Helper functions
# -----------------------------
def build_aho_automaton(sentences: List[str]) -> Automaton:
    A = Automaton()
    for idx, sent in enumerate(sentences):
        if sent.strip():
            A.add_word(sent, (idx, sent))
    A.make_automaton()
    return A

def expand_exact_match(sentence: str, source_text: str, max_len: int = 500) -> str:
    """
    If the original sentence is found inside source_text, expand it forward to capture full context.
    """
    sentence_norm = normalize_text(sentence)
    source_norm = normalize_text(source_text)

    if sentence_norm in source_norm:
        start_idx = source_norm.find(sentence_norm)
        end_idx = start_idx + len(sentence_norm)

        # Expand forward sentence by sentence until max_len or end of text
        source_sents = split_sentences(source_text)
        for s in source_sents:
            s_norm = normalize_text(s)
            if normalize_text(sentence) in s_norm and len(s) > len(sentence):
                expanded_text = s
                return expanded_text[:max_len]
        # Fallback to basic span
        return source_text[start_idx:end_idx]
    return ""

def extract_best_snippet(sentence: str, source_text: str) -> str:
    """
    Return a snippet from source_text that has the highest word overlap with the sentence.
    """
    snippet = expand_exact_match(sentence, source_text)
    if snippet:
        return snippet

    sentence_words = set(sentence.split())
    words = source_text.split()
    max_overlap = 0
    best_start = 0
    best_end = 0
    window_size = len(sentence_words)
    for i in range(len(words) - window_size + 1):
        window_words = set(words[i:i + window_size])
        overlap = len(sentence_words & window_words)
        if overlap > max_overlap:
            max_overlap = overlap
            best_start = i
            best_end = i + window_size
    return " ".join(words[best_start:best_end]) if max_overlap > 0 else source_text[:min(200, len(source_text))]

# -----------------------------
# Evidence Generators
# -----------------------------
def exact_match_evidence(sentences: List[str], source_text: str, source_url: str) -> List[Dict[str, Any]]:
    """
    Generate exact match evidence for sentences found inside source_text.
    Ensures that both original sentence and source snippet are meaningful.
    Applies sentence-level expansion.
    """
    evidence = []
    source_sentences = split_sentences(source_text)
    source_text_norm = normalize_text(source_text)

    for sent in sentences:
        sent_norm = normalize_text(sent)

        # ❗Skip if original sentence itself is not meaningful
        if not is_meaningful_sentence(sent):
            continue

        matched = False

        # 1️⃣ Try full sentence match
        if sent_norm in source_text_norm:
            start_idx = source_text_norm.find(sent_norm)
            end_idx = start_idx + len(sent_norm)
            snippet = source_text[start_idx:end_idx]

            # ❗Check snippet meaningfulness
            if is_meaningful_sentence(snippet):
                sem_score = semantic_similarity(sent, snippet)
                evidence.append({
                    "sentence": sent,
                    "type": "exact_match",
                    "source_text": snippet,
                    "plagiarism_score": 0.99,
                    "semantic_similarity": round(sem_score, 2),
                    "source_url": source_url,
                    "highlights": [{"start": 0, "end": len(snippet), "type": "exact"}]
                })
                matched = True

        # 2️⃣ Sentence-level expansion
        if not matched:
            for i, src_sent in enumerate(source_sentences):
                src_norm = normalize_text(src_sent)

                if sent_norm in src_norm:
                    # Expand one sentence backward and one forward
                    expanded_sents = source_sentences[max(0, i-1): min(len(source_sentences), i+2)]
                    snippet = " ".join(expanded_sents)

                    # ❗Check snippet meaningfulness
                    if not is_meaningful_sentence(snippet):
                        continue

                    sem_score = semantic_similarity(sent, snippet)
                    evidence.append({
                        "sentence": sent,
                        "type": "exact_match",
                        "source_text": snippet,
                        "plagiarism_score": 0.99,
                        "semantic_similarity": round(sem_score, 2),
                        "source_url": source_url,
                        "highlights": [{"start": 0, "end": len(snippet), "type": "exact"}]
                    })
                    break

    return evidence


def paraphrase_match_evidence(sentences: List[str], source_text: str, source_url: str, skip_sents: set) -> List[Dict[str, Any]]:
    evidence = []
    source_text_norm = normalize_text(source_text)
    
    for sent in sentences:
        if sent in skip_sents:
            continue
        
        sent_words = set(sent.split())
        src_words = source_text_norm.split()
        overlap = len(sent_words & set(src_words)) / max(len(sent_words), 1)
        
        if 0.4 <= overlap < 0.99:  # Exclude exact matches
            snippet = extract_best_snippet(sent, source_text_norm)
            sem_score = semantic_similarity(sent, snippet)

            # Promote to exact_match if semantic similarity is high
            ev_type = "exact_match" if (sem_score > 0.85 or overlap > 0.90) else "paraphrased_match"
            
            evidence.append({
                "sentence": sent,
                "type": ev_type,
                "source_text": snippet,
                "plagiarism_score": round(overlap, 2),  # keep original overlap score
                "semantic_similarity": round(sem_score, 2),
                "source_url": source_url,
                "highlights": [{"start": 0, "end": len(snippet), "type": ev_type}]
            })
    
    return evidence


def idea_similarity_evidence(sentence: str) -> Dict[str, Any]:
    return {
        "sentence": sentence,
        "type": "idea_similarity",
        "source_text": "",
        "plagiarism_score": 0.3,
        "semantic_similarity": 0.0,
        "source_url": "",
        "highlights": [{"start": 0, "end": len(sentence), "type": "idea_similarity"}]
    }

# -----------------------------
# Core Module 3 Processing
# -----------------------------
def generate_sentence_level_evidence(block: Dict[str, Any]) -> List[Dict[str, Any]]:
    sentences = split_sentences(block.get("key_sentences", ""))
    evidence_list = []

    exact_matched_sents = set()
    paraphrase_matched_sents = set()

    for candidate in block.get("candidates", []):
        url = candidate.get("url")
        snippet = candidate.get("snippet", "")
        source_text = fetch_full_text(url) or snippet
        if not source_text:
            continue

        # 1️⃣ Exact matches
        exact_evs = exact_match_evidence(sentences, source_text, url)
        evidence_list.extend(exact_evs)
        exact_matched_sents.update(ev["sentence"] for ev in exact_evs)

        # 2️⃣ Paraphrased matches only for sentences without exact matches
        remaining_for_paraphrase = [s for s in sentences if s not in exact_matched_sents]
        paraphrased_evs = paraphrase_match_evidence(remaining_for_paraphrase, source_text, url, skip_sents=set())
        evidence_list.extend(paraphrased_evs)
        paraphrase_matched_sents.update(ev["sentence"] for ev in paraphrased_evs)

    # 3️⃣ Idea similarity only for sentences that got neither exact nor paraphrased matches
    for sent in sentences:
        if sent not in exact_matched_sents and sent not in paraphrase_matched_sents:
            evidence_list.append(idea_similarity_evidence(sent))

    return evidence_list

def process_module3(module2_json: Dict[str, Any]) -> Dict[str, Any]:
    results = []
    doc_id = module2_json.get("doc_id", "unknown")
    for block in module2_json.get("blocks", []):
        evidence = generate_sentence_level_evidence(block)
        results.append({
            "block_id": block.get("block_id"),
            "evidence": evidence
        })
    return {"doc_id": doc_id, "results": results}
