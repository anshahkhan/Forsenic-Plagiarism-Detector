# src/api/metadata_api.py
from fastapi import APIRouter, HTTPException
from typing import List
from src.similarity_search.cleanjson import clean_module3_output
from src.RefinedOutput.callLLM import call_llm_for_metadata

# ✅ import models from module3_models
from src.models.module3_models import Module3Input, Module3Item, BlockInput

router = APIRouter(prefix="/UI-JSON", tags=["JsonUI"])

# ---------------------------
#  Pydantic Models
# ---------------------------


# ---------------------------
#  MAIN ENDPOINT — CLEAN + METADATA
# ---------------------------

@router.post("/metadata_enrich")
async def metadata_enrich(payload: Module3Input):
    try:
        module3_items: List[Module3Item] = []

        # Flatten all evidence
        for block in payload.results:
            for ev in block.evidence:
                module3_items.append(ev)

        # CLEAN STEP — include user_file_offsets
        cleaned_blocks = clean_module3_output(module3_items)

        # Extract all URLs
        urls = set()
        for blk in cleaned_blocks:
            for src in blk["sources"]:
                if src["source_url"]:
                    urls.add(src["source_url"])

        # Call LLM for metadata
        metadata_map = call_llm_for_metadata(list(urls))

        # Attach metadata to each source
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

        return {
            "doc_id": payload.doc_id,
            "results": cleaned_blocks
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Metadata enrichment failed: {str(e)}"
        )
