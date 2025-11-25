from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import json
import os

from src.similarity_search.module3_engine import process_module3

router = APIRouter(
    prefix="/similarity/forsenics",
    tags=["forsenics"]
)

UPLOAD_DIR = os.environ.get("DF_UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# -----------------------------------------------------------
#  POST: JSON INPUT + RAW TEXT INCLUDED
# -----------------------------------------------------------
@router.post("/from_json")
async def module3_from_json(module2_output: dict):
    """
    Accepts Module 2 output and runs Module 3 with raw_text included.
    Expected format:
    {
        "raw_text": "...",
        "blocks": [...]
    }
    """
    if "blocks" not in module2_output:
        raise HTTPException(
            status_code=400,
            detail="Invalid input: expected JSON with 'blocks' field."
        )

    # Extract raw text (required)
    raw_text = module2_output.get("raw_text")
    if not raw_text:
        raise HTTPException(
            status_code=400,
            detail="'raw_text' field is missing. Please include raw_text in the JSON."
        )

    try:
        result = await process_module3(module2_output, raw_text=raw_text)
        return JSONResponse(content=result)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Module 3 processing failed: {str(e)}"
        )


# -----------------------------------------------------------
#  POST: UPLOAD JSON FILE + RAW TEXT IN FILE
# -----------------------------------------------------------
@router.post("/from_file")
async def module3_from_file(file: UploadFile = File(...)):
    """
    Accepts a JSON file containing:
    {
        "raw_text": "...",
        "blocks": [...]
    }
    """
    filename = getattr(file, "filename", None)
    if not filename or not filename.lower().endswith(".json"):
        raise HTTPException(status_code=400, detail="Only JSON files are accepted")

    try:
        content = await file.read()
        module2_json = json.loads(content)

        # Validate
        if "blocks" not in module2_json:
            raise HTTPException(
                status_code=400,
                detail="Invalid file: Missing 'blocks' field."
            )

        raw_text = module2_json.get("raw_text")
        if not raw_text:
            raise HTTPException(
                status_code=400,
                detail="JSON file missing 'raw_text'. Add raw_text."
            )

        # Run Module 3
        result = await process_module3(module2_json, raw_text=raw_text)

        return JSONResponse(content=result)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Module 3 processing failed: {str(e)}"
        )
