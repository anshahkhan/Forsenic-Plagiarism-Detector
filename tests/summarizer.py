import json
from collections import defaultdict

def summarize_plagiarism_v4(report_json):

    results = report_json.get("results", [])
    total_scores = []
    type_counts = defaultdict(int)
    block_summaries = []
    unique_urls = set()  # Track unique URLs globally

    low_score_threshold = 0.6
    low_score_evidence_count = 0

    for block in results:
        block_id = block.get("block_id")
        evidence_list = block.get("evidence", [])

        if not evidence_list:
            block_summaries.append({
                "block_id": block_id,
                "avg_block_score": 0,
                "highest_block_score": 0,
                "most_plagiarized_sentence": None,
                "evidence_count": 0,
                "types_in_block": {}
            })
            continue

        block_scores = []
        block_type_counts = defaultdict(int)
        best_sentence = None
        best_score = 0

        for ev in evidence_list:
            score = ev.get("plagiarism_score", 0)
            ev_type = ev.get("type", "unknown")
            url = ev.get("source_url")

            # Track unique URLs globally
            if url:
                unique_urls.add(url)

            # Add to global & block scores
            block_scores.append(score)
            type_counts[ev_type] += 1
            total_scores.append(score)
            block_type_counts[ev_type] += 1

            # Count low-score evidence
            if score < low_score_threshold:
                low_score_evidence_count += 1

            # Track highest sentence
            if score > best_score:
                best_score = score
                best_sentence = ev.get("sentence")

        block_summary = {
            "block_id": block_id,
            "avg_block_score": round(sum(block_scores) / len(block_scores), 3),
            "highest_block_score": round(max(block_scores), 3),
            "most_plagiarized_sentence": best_sentence,
            "evidence_count": len(evidence_list),
            "types_in_block": dict(block_type_counts)
        }
        block_summaries.append(block_summary)

    # Global summary
    avg_score = round(sum(total_scores) / len(total_scores), 3) if total_scores else 0
    highest_score = round(max(total_scores), 3) if total_scores else 0

    summary = {
        "total_blocks": len(results),
        "total_evidence": len(total_scores),
        "avg_plagiarism_score": avg_score,
        "highest_plagiarism_score": highest_score,
        "low_score_evidence_count": low_score_evidence_count,
        "type_distribution": dict(type_counts),
        "blocks": block_summaries,
        "unique_urls": list(unique_urls),           # List of unique URLs
        "unique_url_count": len(unique_urls)        # Count of unique URLs
    }

    return summary


# Example usage
if __name__ == "__main__":
    with open("plag_output.json", "r") as f:
        data = json.load(f)

    summary = summarize_plagiarism_v4(data)
    print(json.dumps(summary, indent=4))
