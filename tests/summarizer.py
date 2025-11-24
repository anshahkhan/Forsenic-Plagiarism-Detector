import json
from collections import defaultdict

def summarize_plagiarism_v6(report_json):
    """
    Summarize plagiarism results for a list of sentences with sources.
    Handles both dict objects and JSON-string-wrapped dicts.
    """
    # Ensure each item is a dict
    parsed_results = []
    for block in report_json:
        if isinstance(block, str):
            try:
                block = json.loads(block)
            except json.JSONDecodeError:
                # Skip invalid strings
                continue
        if isinstance(block, dict):
            parsed_results.append(block)

    total_scores = []
    type_counts = defaultdict(int)
    block_summaries = []
    unique_urls = set()
    low_score_threshold = 0.6
    low_score_evidence_count = 0

    for block_id, block in enumerate(parsed_results, start=1):
        sentence_text = block.get("sentence")
        sources = block.get("sources", [])

        if not sources:
            block_summaries.append({
                "block_id": block_id,
                "sentence": sentence_text,
                "avg_block_score": 0,
                "highest_block_score": 0,
                "most_plagiarized_source": None,
                "evidence_count": 0,
                "types_in_block": {}
            })
            continue

        block_scores = []
        block_type_counts = defaultdict(int)
        best_source = None
        best_score = 0

        for src in sources:
            # Use aggregated score if available; else compute as (semantic + plagiarism)/2
            score = src.get("score")
            if score is None:
                sem = src.get("semantic_similarity", 0)
                plag = src.get("plagiarism_score", 0)
                score = (sem + plag) / 2

            # Determine type from highlights
            highlights = src.get("highlights", [])
            ev_type = highlights[0]["type"] if highlights else "unknown"

            url = src.get("source_url")
            if url:
                unique_urls.add(url)

            block_scores.append(score)
            type_counts[ev_type] += 1
            block_type_counts[ev_type] += 1
            total_scores.append(score)

            if score < low_score_threshold:
                low_score_evidence_count += 1

            if score > best_score:
                best_score = score
                best_source = src

        block_summary = {
            "block_id": block_id,
            "sentence": sentence_text,
            "avg_block_score": round(sum(block_scores) / len(block_scores), 3),
            "highest_block_score": round(max(block_scores), 3),
            "most_plagiarized_source": best_source,
            "evidence_count": len(sources),
            "types_in_block": dict(block_type_counts)
        }
        block_summaries.append(block_summary)

    # Global summary
    avg_score = round(sum(total_scores) / len(total_scores), 3) if total_scores else 0
    highest_score = round(max(total_scores), 3) if total_scores else 0

    summary = {
        "total_blocks": len(parsed_results),
        "total_evidence": len(total_scores),
        "avg_plagiarism_score": avg_score,
        "highest_plagiarism_score": highest_score,
        "low_score_evidence_count": low_score_evidence_count,
        "type_distribution": dict(type_counts),
        "blocks": block_summaries,
        "unique_urls": list(unique_urls),
        "unique_url_count": len(unique_urls)
    }

    return summary


# Example usage
if __name__ == "__main__":
    with open("plag_output.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    summary = summarize_plagiarism_v6(data)
    print(json.dumps(summary, indent=4))
