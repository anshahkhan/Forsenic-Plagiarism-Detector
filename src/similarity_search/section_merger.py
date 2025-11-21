import re
from typing import List, Dict
import uuid
from . import configs

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

def auto_chunk_section(text: str) -> List[Dict]:
    """
    Automatically splits section text into chunks of TARGET_WORDS_PER_CHUNK
    """
    if not text.strip():
        return []

    words = re.sub(r'\s+', ' ', text).strip().split()
    chunks = []
    start_idx = 0
    chunk_counter = 1

    while start_idx < len(words):
        end_idx = start_idx + getattr(configs, "TARGET_WORDS_PER_CHUNK", 150)
        chunk_words = words[start_idx:end_idx]
        chunk_text = " ".join(chunk_words)
        chunk_id = f"chunk_{chunk_counter}_{uuid.uuid4().hex[:8]}"
        chunks.append({
            "chunk_id": chunk_id,
            "text": chunk_text,
            "word_count": len(chunk_words)
        })
        start_idx = end_idx
        chunk_counter += 1

    return chunks
