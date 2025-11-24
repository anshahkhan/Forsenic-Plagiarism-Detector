# src/api/metadata_api.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Any

from src.similarity_search.cleanjson import clean_module3_output
from src.RefinedOutput.callLLM import call_llm_for_metadata


router = APIRouter(prefix="/UI-JSON", tags=["JsonUI"])


# ---------------------------
#  Pydantic Models
# ---------------------------

class Highlight(BaseModel):
    start: int
    end: int
    type: str


class Module3Item(BaseModel):
    sentence: str
    type: str
    source_text: str
    plagiarism_score: float
    semantic_similarity: float
    source_url: str
    highlights: List[Highlight] = []


class BlockInput(BaseModel):
    block_id: str
    evidence: List[Module3Item]


class Module3Input(BaseModel):
    doc_id: str
    results: List[BlockInput]
    

# ---------------------------
#  MAIN ENDPOINT — CLEAN + METADATA
# ---------------------------

@router.post("/metadata_enrich")
async def metadata_enrich(payload: Module3Input):
    try:
        module3_items: List[Module3Item] = []

        # Flatten all evidence into a single list
        for block in payload.results:
            for ev in block.evidence:
                module3_items.append(ev)

        # CLEAN STEP — returns list[dict]
        cleaned_blocks = clean_module3_output(module3_items)

        # Extract URLs
        urls = set()
        for blk in cleaned_blocks:
            for src in blk["sources"]:
                if src["source_url"]:
                    urls.add(src["source_url"])

        urls = list(urls)

        # Ask Perplexity for metadata
        metadata_map = call_llm_for_metadata(urls)

        # Attach metadata to every source
        for blk in cleaned_blocks:
            for src in blk["sources"]:
                url = src["source_url"]

                src["metadata"] = metadata_map.get(
                    url,
                    {
                        "author": "Unknown",
                        "publication_date": "Unknown",
                        "document_type": "Unknown",
                        "citation": f"Citation for {url}"
                    }
                )

        return {"doc_id": payload.doc_id, "results": cleaned_blocks}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Metadata enrichment failed: {str(e)}"
        )
