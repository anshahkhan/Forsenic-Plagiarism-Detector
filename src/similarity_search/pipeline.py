import json
import logging
from typing import Dict, List
from .section_merger import merge_chunks_to_blocks, auto_chunk_section
from .query_generator import generate_query_for_block
from .perplexity_client import call_perplexity
from .google_client import search_google, search_bing
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

        for block in blocks:
            qres = generate_query_for_block(block)
            query = qres["query"]
            key_sentences = qres["key_sentences"]

            # --- Candidate retrieval ---
            try:
                perplex_results = call_perplexity(query, top_k=configs.TOP_K_RESULTS)
            except Exception as e:
                logger.warning("Perplexity call failed: %s", e)
                perplex_results = []

            do_fallback = _choose_fallback(perplex_results, getattr(configs, "PERPLEXITY_CONFIDENCE_THRESHOLD", 0.5))
            used_results = []

            if not do_fallback and perplex_results:
                for r in perplex_results:
                    r["source_origin"] = "perplexity"
                used_results = perplex_results[:configs.TOP_K_RESULTS]
            else:
                google_results = search_google(query, top_k=configs.TOP_K_RESULTS)
                if google_results:
                    for r in google_results:
                        r["source_origin"] = "google_api"
                    used_results = google_results[:configs.TOP_K_RESULTS]
                else:
                    bing_results = search_bing(query, top_k=configs.TOP_K_RESULTS)
                    for r in bing_results:
                        r["source_origin"] = "bing_api"
                    used_results = bing_results[:configs.TOP_K_RESULTS]

            matches = []
            for candidate in used_results:
                url = candidate.get("url")
                title = candidate.get("title")
                snippet = candidate.get("snippet") or ""
                article_text = fetch_full_text(url) if url else snippet
                if not article_text:
                    article_text = snippet

                embed_sim, ngram_sim, combined, exact_sim = score_text_pair(block["text"], article_text)
                confidence_label = _label_from_score(combined)

                matches.append({
                    "url": url,
                    "title": title,
                    "snippet": snippet,
                    "similarity": float(combined),
                    "embedding_similarity": float(embed_sim),
                    "ngram_similarity": float(ngram_sim),
                    "exact_match_score": float(exact_sim),
                    "confidence_label": confidence_label,
                    "source": candidate.get("source_origin", "unknown"),
                    "source_confidence_raw": candidate.get("score")
                })

            matches = sorted(matches, key=lambda x: x["similarity"], reverse=True)[:configs.TOP_K_RESULTS]

            out["blocks"].append({
                "block_id": block["block_id"],
                "section": sec_name,
                "source_chunk_ids": block.get("source_chunk_ids", []),
                "word_count": block.get("word_count", 0),
                "query": query,
                "key_sentences": key_sentences,
                "matches": matches
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
