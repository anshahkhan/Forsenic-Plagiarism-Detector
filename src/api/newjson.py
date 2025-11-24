# src/api/similarity_api.py  (PATCH / addition)
from fastapi import APIRouter, Body, Query, HTTPException
from fastapi import APIRouter, UploadFile, File

from typing import List, Optional

from src.models.module3_models import Module3Item, CleanedSentence
from src.similarity_search.cleanjson import clean_module3_output
import json

router = APIRouter(
    prefix="/similarity/New-json",
    tags=["New-json"]
)

@router.post("/clean_module3_file", response_model=List[CleanedSentence])
async def clean_module3_file(file: UploadFile = File(..., description="JSON file containing Module 3 output")):
    """
    Accepts a Module 3 JSON file with structure:
    {
        "doc_id": "...",
        "results": [
            {
                "block_id": "...",
                "evidence": [ ... ]
            }
        ]
    }
    Returns cleaned UI-ready JSON with:
      - Each sentence occurrence scored individually
      - Keep all occurrences if <=3
      - Keep top 3 occurrences if >3
    """
    try:
        contents = await file.read()
        module3_json = json.loads(contents)

        # flatten all evidence items
        evidence_items: List[Module3Item] = []
        for block in module3_json.get("results", []):
            for ev in block.get("evidence", []):
                if isinstance(ev, dict):
                    evidence_items.append(Module3Item(**ev))

        if not evidence_items:
            raise HTTPException(status_code=400, detail="No evidence found in file")

        # clean using updated logic
        cleaned: List[CleanedSentence] = clean_module3_output(evidence_items)

        return cleaned

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {e}")