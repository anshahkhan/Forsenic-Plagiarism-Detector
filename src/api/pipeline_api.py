from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import json
import os
import requests
from pydantic import BaseModel

from src.ingestion.utils import normalize_file_path
from src.ingestion.parsers import parse_pdf, parse_docx, parse_html, parse_text_file
from src.similarity_search.pipeline import process_document
from src.similarity_search.module3_engine import process_module3
from src.similarity_search.highlighter import enrich_module3_with_user_offsets, process_module3_with_user_offsets

router = APIRouter(
    prefix="/pipeline",
    tags=["pipeline"]
)

UPLOAD_DIR = os.environ.get("DF_UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


class RawText(BaseModel):
    text: str


@router.post("/full-text")
async def run_full_pipeline_text(payload: RawText):
    """
    Full pipeline for RAW TEXT:
    Text → save .txt → parse → Module2 → Module3 → final JSON.
    """
    try:
        text = payload.text.strip()
        if not text:
            raise HTTPException(status_code=400, detail="Text input is empty.")

        import uuid
        file_id = uuid.uuid4().hex
        filename = f"{file_id}.txt"
        file_path = normalize_file_path(os.path.join(UPLOAD_DIR, filename))

        # --------------------------------
        # 1) Save text to .txt file
        # --------------------------------
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text)

        # --------------------------------
        # 2) Module 1: Parse text file
        # --------------------------------
        module1_json = parse_text_file(file_path)

        # --------------------------------
        # 3) Module 2: Similarity Search
        # --------------------------------
        module2_json = process_document(module1_json)

        # --------------------------------
        # 4) Module 3: Forensic Matching
        # --------------------------------

        # Pass the original text for offsets
        module3_json = await process_module3(module2_json, raw_text=module1_json["raw_text"])
        # module3_json = await process_module3(module2_json)

        # --------------------------------
        # 5) Final return
        # --------------------------------
        return JSONResponse(content={
            "file_id": file_id,
            "module1": module1_json,
            "module2": module2_json,
            "module3": module3_json
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")

@router.post("/full")
async def run_full_pipeline(file: UploadFile = File(...)):
    """
    Full automatic pipeline:
    Upload file → Module1 → Module2 → Module3 → return final JSON.
    """
    try:
        # -----------------------------
        # 1) Save uploaded file
        # -----------------------------
        import uuid
        file_id = uuid.uuid4().hex
        filename = f"{file_id}_{file.filename}"
        file_path = normalize_file_path(os.path.join(UPLOAD_DIR, filename))

        with open(file_path, "wb") as f:
            f.write(await file.read())

        # -----------------------------
        # 2) Module 1: Parse the file
        # -----------------------------
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".pdf":
            module1_json = parse_pdf(file_path)
        elif ext == ".docx":
            module1_json = parse_docx(file_path)
        elif ext in [".html", ".htm"]:
            module1_json = parse_html(file_path)
        elif ext == ".txt":
            module1_json = parse_text_file(file_path)
        else:
            raise HTTPException(400, f"Unsupported file type: {ext}")

        # -----------------------------
        # 3) Module 2: Similarity Search
        # -----------------------------
        module2_json = process_document(module1_json)

        # -----------------------------
        # 4) Module 3: Forensics
        # -----------------------------

        module3_json = await process_module3(module2_json, raw_text=module1_json["raw_text"])
        # module3_json = await process_module3(module2_json)

        # -----------------------------
        # 5) Return final result
        # -----------------------------
        return JSONResponse(content={
            "module1": module1_json,
            "module2": module2_json,
            "module3": module3_json
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
