# src/api/evidence_api.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import json
import tempfile
import os
from src.similarity_search.module3_engine import generate_plagiarism_report  # Module 3 core

router = APIRouter(
    prefix="/evidence",
    tags=["plagiarism_evidence"]
)

# -----------------------------
# Endpoint: JSON file upload
# -----------------------------
@router.post("/from_file")
async def evidence_from_file(file: UploadFile = File(...)):
    """
    Accepts a Module 2 JSON file, runs Module 3 evidence extraction,
    and returns the evidence-ready JSON separately.
    """
    filename = getattr(file, "filename", None)
    if not filename or not filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Only JSON files are accepted.")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
            tmp.write(await file.read())
            tmp.flush()
            tmp_path = tmp.name

        with open(tmp_path, "r", encoding="utf-8") as f:
            module2_output = json.load(f)

        module3_output = generate_plagiarism_report(module2_output)
        os.remove(tmp_path)
        return JSONResponse(content=module3_output)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


# -----------------------------
# Endpoint: JSON body input
# -----------------------------
@router.post("/from_json")
async def evidence_from_json(doc: dict):
    """
    Accepts Module 2 JSON directly, runs Module 3 evidence extraction,
    returns Module 3 output JSON separately.
    """
    try:
        module3_output = generate_plagiarism_report(doc)
        return JSONResponse(content=module3_output)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
