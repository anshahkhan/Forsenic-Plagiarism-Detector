# src/api/similarity_api.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import json
import tempfile
import os
from src.similarity_search.pipeline import process_document
from src.similarity_search.module3_engine import process_module3  # Module 3

router = APIRouter(
    prefix="/similarity",
    tags=["similarity_search"]
)

@router.post("/from_file")
async def similarity_from_file(file: UploadFile = File(...)):
    """
    Accepts a Module 1 JSON file upload (can be raw without pre-chunked sections),
    runs Module 2 similarity search (auto-chunking sections if needed),
    and returns the result JSON.
    """
    filename = getattr(file, "filename", None)
    if not filename or not filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Only JSON files are accepted.")

    try:
        # Read uploaded file into temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
            tmp.write(await file.read())
            tmp.flush()
            tmp_path = tmp.name

        # Load JSON and run Module 2 pipeline (process_document handles auto-chunking)
        with open(tmp_path, "r", encoding="utf-8") as f:
            doc_json = json.load(f)

        output = process_document(doc_json)

        os.remove(tmp_path)
        return JSONResponse(content=output)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.post("/from_json")
async def similarity_from_json(doc: dict):
    """
    Accepts a JSON payload (Module 1 output or raw sections without chunks) directly in request body,
    runs Module 2 similarity search (auto-chunking sections if needed),
    and returns the result JSON.
    """
    try:
        output = process_document(doc)
        return JSONResponse(content=output)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


