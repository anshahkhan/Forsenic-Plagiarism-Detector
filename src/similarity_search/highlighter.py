# highlighter.py
import logging
from typing import Dict, Any, List, Optional
from src.ingestion.utils import split_sentences_with_offsets

logger = logging.getLogger(__name__)

def get_user_file_offsets(matched_sentence: str, user_sentences: List[Dict[str, Any]]) -> Optional[Dict[str, int]]:
    """
    Returns the start and end offsets of the matched sentence in the user file.
    """
    for s in user_sentences:
        if matched_sentence in s["sentence"]:
            return {"start": s["start"], "end": s["end"]}
    return None

def enrich_module3_with_user_offsets(module3_json: Dict[str, Any], user_file_text: str) -> Dict[str, Any]:
    """
    For each evidence in module3, add 'user_file_offsets' relative to the full user-submitted file.
    """
    if not module3_json or not user_file_text:
        return module3_json

    user_sentences = split_sentences_with_offsets(user_file_text)

    for result in module3_json.get("results", []):
        for evidence in result.get("evidence", []):
            sentence = evidence.get("sentence", "")
            offsets = get_user_file_offsets(sentence, user_sentences)
            if offsets:
                evidence["user_file_offsets"] = offsets
            else:
                evidence["user_file_offsets"] = {"start": -1, "end": -1}
                logger.warning("Sentence not found in user file: %s", sentence)

    return module3_json

async def process_module3_with_user_offsets(module2_json: Dict[str, Any], user_file_text: str, **kwargs) -> Dict[str, Any]:
    """
    Wrapper around module3_engine.process_module3 that enriches evidence with user file offsets.
    """
    from src.similarity_search.module3_engine import process_module3

    module3_json = await process_module3(module2_json, **kwargs)
    enriched = enrich_module3_with_user_offsets(module3_json, user_file_text)
    return enriched
