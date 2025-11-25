# src/similarity_search/module3_cleaner.py
from collections import defaultdict
from typing import List, Dict, Any
from src.models.module3_models import Module3Item, UserFileOffset


def _compute_score(item: Module3Item) -> float:
    sem = item.semantic_similarity if item.semantic_similarity is not None else 0.0
    plag = item.plagiarism_score if item.plagiarism_score is not None else 0.0
    return (sem + plag) / 2.0


def clean_module3_output(items: List[Module3Item]) -> List[Dict[str, Any]]:
    """
    Clean Module 3 output and return as list of dicts:

    1. Each sentence occurrence gets its own score = (semantic + plagiarism)/2.
    2. If sentence repeats 1–3 times: keep all.
    3. If sentence repeats >3 times: keep top 3 by score.
    4. Returns list of dicts with keys:
       sentence, sources (list of dicts), occurrences
    """
    grouped = defaultdict(list)

    # Group items by sentence
    for item in items:
        grouped[item.sentence].append(item)

    cleaned_sentences: List[Dict[str, Any]] = []

    for sentence, evidences in grouped.items():
        scored_sources: List[Dict[str, Any]] = []

        for ev in evidences:
            score = _compute_score(ev)

            # Ensure user_file_offsets is a proper UserFileOffset object or None
            user_offsets = None
            if ev.user_file_offsets:
                if isinstance(ev.user_file_offsets, dict):
                    user_offsets = UserFileOffset(**ev.user_file_offsets)
                elif isinstance(ev.user_file_offsets, UserFileOffset):
                    user_offsets = ev.user_file_offsets

            scored_sources.append({
                "source_text": ev.source_text,
                "source_url": ev.source_url,
                # "plagiarism_score": ev.plagiarism_score,
                # "semantic_similarity": ev.semantic_similarity,
                "score": round(score, 4),
                "user_file_offsets": user_offsets
            })

        # Keep top 3 sources if more than 3
        if len(scored_sources) > 3:
            scored_sources.sort(key=lambda s: s["score"], reverse=True)
            scored_sources = scored_sources[:3]

        cleaned_sentences.append({
            "sentence": sentence,
            "sources": scored_sources,
            "occurrences": len(evidences)
        })

    return cleaned_sentences
