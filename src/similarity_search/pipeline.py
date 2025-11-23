import json
import logging
from typing import Dict, List
from .section_merger import merge_chunks_to_blocks, auto_chunk_section
from .query_generator import generate_query_for_block
from .perplexity_client import call_perplexity
from .google_client import search_google, search_bing, search_google_advanced
from .web_fetcher import fetch_full_text
from .similarity_engine import score_text_pair
from . import configs
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def _choose_fallback(perplexity_results: List[Dict], threshold: float) -> bool:
    if not perplexity_results:
        return True
    scores = [float(r.get("score", 1.0)) for r in perplexity_results]  # default 1.0
    max_score = max(scores) if scores else 0
    return max_score < threshold


def _label_from_score(score: float) -> str:
    if score >= getattr(configs, "CONFIDENCE_HIGH_THRESHOLD", 0.85):
        return "high"
    if score >= getattr(configs, "CONFIDENCE_MED_THRESHOLD", 0.6):
        return "medium"
    return "low"

def process_document(doc: Dict) -> Dict:
    doc_id = doc.get("doc_id", "unknown")
    out = {"doc_id": doc_id, "blocks": []}

    for section in doc.get("sections", []):
        sec_name = section.get("name", "section")
        chunks = section.get("chunks")

        if not chunks:
            text = section.get("text", "")
            if not text.strip():
                continue
            chunks = auto_chunk_section(text)

        blocks = merge_chunks_to_blocks(
            chunks,
            target_words=configs.TARGET_WORDS_PER_BLOCK,
            min_words=configs.MIN_WORDS_PER_BLOCK,
            max_words=configs.MAX_WORDS_PER_BLOCK
        )

        # Limit Google usage
        max_google_chunks = getattr(configs, "MAX_GOOGLE_CHUNKS", 3)

        for idx, block in enumerate(blocks):
            # -------------------------
            # Generate query and key sentences first
            # -------------------------
            qres = generate_query_for_block(block)
            query = qres["query"]
            key_sentences = qres["key_sentences"]

            # -------------------------
            # 1. GOOGLE ADVANCED SEARCH (limited)
            # -------------------------
            google_results = []
            if idx < max_google_chunks and key_sentences.strip():
                try:
                    # Use key sentences for all_words or important_words
                    google_results = search_google_advanced(
                        all_words=key_sentences,       # split keywords automatically
                        important_words=key_sentences, # optional: emphasize these words
                        top_k=configs.TOP_K_RESULTS
                    )
                    for r in google_results:
                        r["source"] = "google_advanced"
                except Exception as e:
                    logger.warning("Google Advanced search failed: %s", e)

            # Track URLs to avoid duplicates
            seen_urls = {r.get("url") for r in google_results if r.get("url")}

            # -------------------------
            # 2. PERPLEXITY (normal logic — unchanged)
            # -------------------------
            try:
                perplex_results = call_perplexity(query, top_k=configs.TOP_K_RESULTS)
            except Exception as e:
                logger.warning("Perplexity call failed: %s", e)
                perplex_results = []

            # Remove duplicates from Perplexity results
            filtered_perplex = []
            for r in perplex_results:
                if r.get("url") not in seen_urls:
                    r["source"] = "perplexity"
                    filtered_perplex.append(r)
                    seen_urls.add(r.get("url"))

            # -------------------------
            # 3. Combine: final candidates for this block
            # -------------------------
            candidate_urls = google_results + filtered_perplex

            # Keep only essential metadata
            cleaned_candidates = []
            for c in candidate_urls:
                cleaned_candidates.append({
                    "url": c.get("url"),
                    "title": c.get("title"),
                    "snippet": c.get("snippet"),
                    "source": c.get("source")
                })

            # -------------------------
            # 4. Save block output
            # -------------------------
            out["blocks"].append({
                "block_id": block["block_id"],
                "section": sec_name,
                "source_chunk_ids": block.get("source_chunk_ids", []),
                "word_count": block.get("word_count", 0),
                "query": query,
                "key_sentences": key_sentences,
                "candidates": cleaned_candidates
            })


    return out


def run_from_file(input_path: str, output_path: str):
    with open(input_path, "r", encoding="utf-8") as f:
        doc = json.load(f)
    res = process_document(doc)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    return res

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run enhanced similarity search pipeline on Module 1 JSON")
    parser.add_argument("--input", "-i", required=True, help="Input JSON file path from Module 1")
    parser.add_argument("--output", "-o", default="module2_output.json", help="Output JSON file path for Module 2 results")
    args = parser.parse_args()
    res = run_from_file(args.input, args.output)
    logger.info("Processing completed. Results saved to %s", args.output)
