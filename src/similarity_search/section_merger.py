import re
from typing import List, Dict
import uuid
from . import configs


def split_sentences_fallback(text: str):
    return re.split(r'(?<=[.!?])\s+', text)



def word_count(text: str) -> int:
    return len(re.findall(r"\w+", text))

def merge_chunks_to_blocks(chunks: List[Dict],
                           target_words=300,
                           min_words=200,
                           max_words=400) -> List[Dict]:
    """
    Merge small chunks into blocks of 200–400 words.
    Each block keeps track of source chunk IDs and word count.
    """
    blocks = []
    current_texts = []
    current_ids = []
    current_wc = 0
    block_idx = 0

    for chunk in chunks:
        text = chunk.get("text", "").strip()
        cid = chunk.get("id") or chunk.get("chunk_id")
        w = word_count(text)

        # Split oversized chunks
        if w > max_words:
            sentences = re.split(r'(?<=[.!?])\s+', text)
            temp_text = ""
            temp_wc = 0
            for s in sentences:
                sw = word_count(s)
                if temp_wc + sw > max_words and temp_text:
                    blocks.append({
                        "block_id": f"block_{block_idx}",
                        "text": temp_text.strip(),
                        "source_chunk_ids": [cid],
                        "word_count": temp_wc
                    })
                    block_idx += 1
                    temp_text = s
                    temp_wc = sw
                else:
                    temp_text += (" " if temp_text else "") + s
                    temp_wc += sw
            if temp_text:
                blocks.append({
                    "block_id": f"block_{block_idx}",
                    "text": temp_text.strip(),
                    "source_chunk_ids": [cid],
                    "word_count": temp_wc
                })
                block_idx += 1
            continue

        # Merge into current block if under max_words
        if current_wc + w <= max_words:
            current_texts.append(text)
            if cid:
                current_ids.append(cid)
            current_wc += w
        else:
            if current_texts:
                blocks.append({
                    "block_id": f"block_{block_idx}",
                    "text": " ".join(current_texts).strip(),
                    "source_chunk_ids": current_ids,
                    "word_count": current_wc
                })
                block_idx += 1
            current_texts = [text]
            current_ids = [cid] if cid else []
            current_wc = w

    # Add remaining block
    if current_texts:
        blocks.append({
            "block_id": f"block_{block_idx}",
            "text": " ".join(current_texts).strip(),
            "source_chunk_ids": current_ids,
            "word_count": current_wc
        })

    # Merge blocks that are too small
    merged = []
    i = 0
    while i < len(blocks):
        blk = blocks[i]
        if blk["word_count"] < min_words and i + 1 < len(blocks):
            nxt = blocks[i+1]
            merged_text = f"{blk['text']} {nxt['text']}"
            merged_ids = blk['source_chunk_ids'] + nxt['source_chunk_ids']
            merged_wc = blk['word_count'] + nxt['word_count']
            merged.append({
                "block_id": f"block_{len(merged)}",
                "text": merged_text.strip(),
                "source_chunk_ids": merged_ids,
                "word_count": merged_wc
            })
            i += 2
        else:
            blk["block_id"] = f"block_{len(merged)}"
            merged.append(blk)
            i += 1

    return merged

def auto_chunk_section(
    text: str,
    target_words: int = 150,
    overlap_ratio: float = 0.3,
    max_expand: int = 40,
) -> List[Dict]:
    """
    Smarter chunker for plagiarism detection.

    ✔ Uses overlapping windows (default overlap = 30%)
    ✔ Tries to end chunk on sentence boundaries
    ✔ Soft-expands to finish the sentence (max +40 words)
    ✔ Prevents splitting plagiarized text across chunks
    """

    if not text.strip():
        return []

    # Normalize whitespace
    words = re.sub(r"\s+", " ", text).strip().split()
    num_words = len(words)

    # Overlap count
    overlap_words = int(target_words * overlap_ratio)

    chunks = []
    start = 0
    chunk_counter = 1

    while start < num_words:

        # Raw chunk
        raw_end = min(start + target_words, num_words)
        chunk_words = words[start:raw_end]

        # Try sentence boundary alignment
        chunk_text = " ".join(chunk_words)
        sentences = split_sentences_fallback(chunk_text)
    

        # If more than 1 sentence, use full last sentence to close chunk
        if len(sentences) > 1:
            # If last sentence is short, include it to avoid cutting in half
            last_sentence = sentences[-1].split()
            if len(last_sentence) < max_expand:
                chunk_words = words[start : start + len(" ".join(sentences).split())]

        # Create final text
        final_chunk_text = " ".join(chunk_words)

        # Assign chunk ID
        chunk_id = f"chunk_{chunk_counter}_{uuid.uuid4().hex[:8]}"

        chunks.append({
            "chunk_id": chunk_id,
            "text": final_chunk_text,
            "word_count": len(chunk_words)
        })

        # Move the window with overlap
        start = start + target_words - overlap_words
        chunk_counter += 1

    return chunks