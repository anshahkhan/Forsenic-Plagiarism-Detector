# src/api/pipeline_api.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os
import uuid
from fastapi.encoders import jsonable_encoder


from src.ingestion.utils import normalize_file_path
from src.ingestion.parsers import parse_pdf, parse_docx, parse_html, parse_text_file
from src.similarity_search.pipeline import process_document
from src.similarity_search.module3_engine import process_module3

# ✅ Import all module3 models from models, not JsonUI
from src.models.module3_models import Module3Input, BlockInput, Module3Item, UserFileOffset
from src.api.JsonUI import metadata_enrich  # only the enrichment endpoint

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

UPLOAD_DIR = os.environ.get("DF_UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# -----------------------------
# Helper: convert Module3 output -> JsonUI format
# -----------------------------
async def enrich_module3_for_jsonui(module3_json: dict) -> dict:
    blocks: list[BlockInput] = []
    for block in module3_json.get("results", []):
        evidences: list[Module3Item] = []
        for ev in block.get("evidence", []):
            ufo = ev.get("user_file_offsets")
            if isinstance(ufo, dict):
                ev["user_file_offsets"] = UserFileOffset(**ufo)
            evidences.append(Module3Item(**ev))
        blocks.append(BlockInput(block_id=block["block_id"], evidence=evidences))

    payload = Module3Input(
        doc_id=module3_json.get("doc_id", "unknown"),
        results=blocks
    )

    enriched = await metadata_enrich(payload)
    return jsonable_encoder(enriched)

# -----------------------------
# Full pipeline — raw text
# -----------------------------
@router.post("/full-text")
async def run_full_pipeline_text(payload: dict):
    try:
        text = payload.get("text", "").strip()
        if not text:
            raise HTTPException(status_code=400, detail="Text input is empty.")

        # Save text file
        file_id = uuid.uuid4().hex
        file_path = normalize_file_path(os.path.join(UPLOAD_DIR, f"{file_id}.txt"))
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text)

        # Module1
        module1_json = parse_text_file(file_path)

        # Module2
        module2_json = process_document(module1_json)

        # Module3
        module3_json = await process_module3(module2_json, raw_text=module1_json["raw_text"])

        # JsonUI enrichment
        enriched_json = await enrich_module3_for_jsonui(module3_json)

        return JSONResponse(content={
            "file_id": file_id,
            "module1": module1_json,
            "module2": module2_json,
            "module3": enriched_json
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")

# -----------------------------
# Full pipeline — file upload
# -----------------------------
@router.post("/full")
async def run_full_pipeline(file: UploadFile = File(...)):
    try:
        file_id = uuid.uuid4().hex
        filename = f"{file_id}_{file.filename}"
        file_path = normalize_file_path(os.path.join(UPLOAD_DIR, filename))

        with open(file_path, "wb") as f:
            f.write(await file.read())

        # Parse file
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

        # Module2
        module2_json = process_document(module1_json)

        # Module3
        module3_json = await process_module3(module2_json, raw_text=module1_json["raw_text"])

        # JsonUI enrichment
        enriched_json = await enrich_module3_for_jsonui(module3_json)

        return JSONResponse(content={
            "file_id": file_id,
            "module1": module1_json,
            "module2": module2_json,
            "module3": enriched_json
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
