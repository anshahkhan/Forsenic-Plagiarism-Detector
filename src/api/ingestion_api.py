# src/api/ingestion_api.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import Any
import os
import uuid
import shutil
import requests

from src.models.ingestion_models import URLInput, UploadResponse
from src.ingestion.utils import normalize_file_path
from src.ingestion.parsers import parse_pdf, parse_docx, parse_html

router = APIRouter(prefix="/ingestion", tags=["ingestion"])

UPLOAD_DIR = os.environ.get("DF_UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload-file/", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    file_id = uuid.uuid4().hex
    filename = f"{file_id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    file_path = normalize_file_path(file_path)
    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "success", "file_id": file_id, "filename": file.filename, "path": file_path}

@router.post("/fetch-url/", response_model=UploadResponse)
def fetch_url(payload: URLInput):
    r = requests.get(str(payload.url), timeout=15)
    if r.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {r.status_code}")
    file_id = uuid.uuid4().hex
    filename = f"{file_id}.html"
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(r.content)
    return {"status": "success", "file_id": file_id, "filename": filename, "path": file_path}

@router.post("/parse/{file_id}")
def parse_uploaded(file_id: str):
    candidates = [f for f in os.listdir(UPLOAD_DIR) if f.startswith(file_id)]
    if not candidates:
        raise HTTPException(status_code=404, detail="File not found")
    path = os.path.join(UPLOAD_DIR, candidates[0])
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext in [".pdf"]:
            result = parse_pdf(path)
        elif ext in [".docx"]:
            result = parse_docx(path)
        elif ext in [".html", ".htm"]:
            result = parse_html(path)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file extension: {ext}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return JSONResponse(content=result)
