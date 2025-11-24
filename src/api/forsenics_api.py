from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import json
from src.similarity_search.module3_engine import process_module3

router = APIRouter(
    prefix="/similarity/forsenics",
    tags=["forsenics"]
)

@router.post("/from_json")
async def module3_from_json(module2_output: dict):
    """
    Accepts Module 2 output and runs Module 3 evidence extraction.
    """
    if "blocks" not in module2_output:
        raise HTTPException(
            status_code=400,
            detail="Invalid input: expected Module 2 output JSON with 'blocks' field."
        )

    try:
        result = await process_module3(module2_output)
        return JSONResponse(content=result)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Module 3 processing failed: {str(e)}"
        )


@router.post("/from_file")
async def module3_from_file(file: UploadFile = File(...)):
    """
    Accepts a JSON file (Module 2 output) and runs Module 3.
    """
    if not getattr(file, "filename", "").endswith(".json"):
        raise HTTPException(status_code=400, detail="Only JSON files are accepted")

    try:
        content = await file.read()
        module2_json = json.loads(content)

        result = await process_module3(module2_json)
        return JSONResponse(content=result)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Module 3 processing failed: {str(e)}"
        )
