# src/api/newjson.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import json
import asyncio
from ..RefinedOutput.callLLM import call_llm_for_metadata

router = APIRouter(
    prefix="/similarity/New-json",
    tags=["New-json"]
)

# Example response model (optional)
from pydantic import BaseModel

class Highlight(BaseModel):
    start: int
    end: int
    type: str

class Source(BaseModel):
    source_text: str
    source_url: str
    plagiarism_score: float
    semantic_similarity: float
    score: float
    highlights: List[Highlight]
    author: Optional[str] = None
    publication_date: Optional[str] = None
    document_type: Optional[str] = None
    citation: Optional[str] = None

class CleanedSentence(BaseModel):
    sentence: str
    sources: List[Source]
    aggregated_score: float
    occurrences: int


async def query_perplexity_metadata(urls: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Replace this stub with actual Perplexity API/LLM call.
    Return a dict mapping URL -> metadata
    Example:
    {
        "https://example.com": {
            "author": "John Doe",
            "publication_date": "2024-03-15",
            "document_type": "blog",
            "citation": "Doe, J. (2024)..."
        }
    }
    """
    metadata = {}
    for url in urls:
        # TODO: Replace with actual API call
        metadata[url] = {
            "author": "Unknown Author",
            "publication_date": "Unknown Date",
            "document_type": "Unknown",
            "citation": f"Citation for {url}"
        }
    return metadata


@router.post("/clean_module3_file", response_model=List[CleanedSentence])
async def clean_module3_file(file: UploadFile = File(..., description="JSON file containing Module 3 output")):
    try:
        content = await file.read()
        module3_data = json.loads(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON file: {e}")

    # Step 1: Extract all unique URLs
    all_urls = set()
    for sentence_block in module3_data:
        for source in sentence_block.get("sources", []):
            url = source.get("source_url")
            if url:
                all_urls.add(url)
    unique_urls = list(all_urls)

    # Step 2: Query Perplexity for metadata
    metadata_map = await query_perplexity_metadata(unique_urls)

    # Step 3: Merge metadata back into original JSON
    for sentence_block in module3_data:
        for source in sentence_block.get("sources", []):
            url = source.get("source_url")
            if url and url in metadata_map:
                source.update(metadata_map[url])

    return module3_data

@router.post("/test_metadata")
async def test_metadata(file: UploadFile = File(..., description="Upload Module 3 JSON")):
    try:
        content = await file.read()
        module3_data = json.loads(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON file: {e}")

    # Extract unique URLs
    all_urls = set()
    for sentence_block in module3_data:
        for source in sentence_block.get("sources", []):
            url = source.get("source_url")
            if url:
                all_urls.add(url)

    unique_urls = list(all_urls)

    if not unique_urls:
        return {"message": "No URLs found in the uploaded JSON."}

    # Call Perplexity for metadata
    metadata_map = call_llm_for_metadata(unique_urls)

    # Return extracted URLs + metadata for testing
    return {
        "unique_urls": unique_urls,
        "metadata_map": metadata_map
    }