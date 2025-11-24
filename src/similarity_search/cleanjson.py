# src/similarity_search/module3_cleaner.py
from collections import defaultdict
from typing import List, Dict, Any, Optional, Tuple
from src.models.module3_models import Module3Item, CleanedSentence, CleanedSource



def _compute_score(item: Module3Item) -> float:
    sem = item.semantic_similarity 
    plag = item.plagiarism_score
    return (sem + plag) / 2.0


def clean_module3_output(items: List[Module3Item]) -> List[CleanedSentence]:
    """
    Clean Module 3 output according to updated rules:

    1. Each sentence occurrence gets its own score = (semantic + plagiarism)/2.
    2. If sentence repeats 1–3 times: keep all.
    3. If sentence repeats >3 times: keep top 3 by score.
    4. Return list of CleanedSentence, each with top occurrences.
    """
    from collections import defaultdict

    grouped = defaultdict(list)

    # group items by sentence
    for item in items:
        grouped[item.sentence].append(item)

    cleaned_sentences: List[CleanedSentence] = []

    for sentence, evidences in grouped.items():
        # calculate score for each occurrence
        scored_sources: List[CleanedSource] = []
        for ev in evidences:
            score = _compute_score(ev)
            scored_sources.append(
                CleanedSource(
                    source_text=ev.source_text,
                    source_url=ev.source_url,
                    plagiarism_score=ev.plagiarism_score,
                    semantic_similarity=ev.semantic_similarity,
                    score=round(score, 4),
                    highlights=ev.highlights or []
                )
    )

        # if more than 3 occurrences, keep top 3 by score
        if len(scored_sources) > 3:
            scored_sources.sort(key=lambda s: s.score, reverse=True)
            scored_sources = scored_sources[:3]

        # average score across kept sources
        aggregated_score = round(sum(s.score for s in scored_sources) / len(scored_sources), 4)

        cleaned_sentences.append(
            CleanedSentence(
                sentence=sentence,
                sources=scored_sources,
                aggregated_score=aggregated_score,
                occurrences=len(evidences)
            )
        )

    return cleaned_sentences
