# src/api/similarity_api.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import json
import tempfile
import os
from src.similarity_search.pipeline import process_document
from src.similarity_search.module3_engine import process_module3  # Module 3

from typing import List, Dict, Any
router = APIRouter(
    prefix="/similarity",
    tags=["similarity_search"]
)
processed_module3_cache = {}  # key: doc_id, value: processed JSON

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


@router.post("/module3/from_json")
async def module3_from_json(module2_output: dict):
    """
    Accepts Module 2 output (URLs), runs Module 3 to find exact content matches,
    returns Module 3 JSON.
    """
    if "blocks" not in module2_output:
        raise HTTPException(
            status_code=400,
            detail="Invalid input: expected Module 2 output JSON with 'blocks' field."
        )
    try:
        module3_output = process_module3(module2_output)
        return JSONResponse(content=module3_output)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Module 3 processing failed: {str(e)}"
        )


@router.post("/module3/from_file")
async def module3_from_file(file: UploadFile = File(...)):
    """
    Accepts a JSON file (Module 2 output with URLs),
    runs Module 3 forensic evidence extraction,
    returns Module 3 JSON.
    """
    if not getattr(file, "filename", "").endswith(".json"):
        raise HTTPException(status_code=400, detail="Only JSON files are accepted.")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
            tmp.write(await file.read())
            tmp.flush()
            tmp_path = tmp.name

        with open(tmp_path, "r", encoding="utf-8") as f:
            module2_json = json.load(f)

        module3_output = process_module3(module2_json)
        return JSONResponse(content=module3_output)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Module 3 processing failed: {str(e)}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
def process_module3_output(module3_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Cleans Module 3 output for UI.

    For each block/sentence:
        - If multiple evidences exist for the same original sentence,
          apply priority logic:
              exact_match > paraphrased(high confidence) > idea_similarity
        - If only one evidence exists, just return it.
    """

    clean_results = []

    for block in module3_data.get("results", []):
        block_id = block.get("block_id")
        evidences = block.get("evidence", [])

        if not evidences:
            continue

        # 🔍 Group evidences by original sentence
        grouped = {}
        for ev in evidences:
            original_sentence = ev.get("sentence", "").strip()
            grouped.setdefault(original_sentence, []).append(ev)

        # Process each sentence group independently
        for original_sentence, ev_list in grouped.items():

            # If only one evidence → use it directly (NO priority needed)
            if len(ev_list) == 1:
                best = ev_list[0]

            else:
                # -------------------------------
                # MULTIPLE MATCHES → Apply priority
                # -------------------------------

                # 1️⃣ Exact matches
                exacts = [ev for ev in ev_list if ev.get("type") == "exact_match"]
                if exacts:
                    best = max(exacts, key=lambda x: x.get("semantic_similarity", 0))

                else:
                    # 2️⃣ High-confidence paraphrased matches
                    paraphrased = [
                        ev for ev in ev_list
                        if ev.get("type") == "paraphrased_match" and
                           (ev.get("semantic_similarity", 0) >= 0.85 or
                            ev.get("plagiarism_score", 0) >= 0.9)
                    ]
                    if paraphrased:
                        best = max(paraphrased, key=lambda x: x.get("semantic_similarity", 0))
                    else:
                        # 3️⃣ Idea similarity fallback
                        idea = [ev for ev in ev_list if ev.get("type") == "idea_similarity"]
                        if idea:
                            best = max(idea, key=lambda x: x.get("semantic_similarity", 0))
                        else:
                            # Should never happen, but failsafe:
                            best = ev_list[0]

            # Store cleaned result
            clean_results.append({
                "block_id": block_id,
                "original_sentence": best.get("sentence"),
                "source_url": best.get("source_url", ""),
                "source_text": best.get("source_text", ""),
                "match_type": best.get("type", ""),
                "plagiarism_score": best.get("plagiarism_score", 0),
                "semantic_similarity": best.get("semantic_similarity", 0),
                "highlights": best.get("highlights", []),
            })

    return {
        "doc_id": module3_data.get("doc_id", ""),
        "clean_results": clean_results
    }

@router.post("/process_module3_file")
async def process_module3_file(file: UploadFile = File(...)):
    contents = await file.read()
    module3_data = json.loads(contents)
    processed_data = process_module3_output(module3_data)

    # Store in cache for download
    doc_id = processed_data.get("doc_id")
    if doc_id:
        processed_module3_cache[doc_id] = processed_data

    return processed_data


@router.get("/download_clean_json/{doc_id}")
def download_clean_json(doc_id: str):
    if doc_id not in processed_module3_cache:
        raise HTTPException(status_code=404, detail="Processed JSON not found.")
    return JSONResponse(content=processed_module3_cache[doc_id], media_type="application/json")