# src/models/module3_models.py
from typing import List, Optional
from pydantic import BaseModel, Field





class Highlight(BaseModel):
    start: int
    end: int
    type: Optional[str] = None


class UserFileOffset(BaseModel):
    start: int = -1  # or 0 if you prefer
    end: int = -1



class Module3Item(BaseModel):
    """
    Unified model used by:
    - Module 3 Engine
    - Cleaning Layer (cleanjson.py)
    - FastAPI Endpoint (UI JSON)
    """
    sentence: str
    type: Optional[str] = None
    source_text: Optional[str] = None
    plagiarism_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    semantic_similarity: Optional[float] = Field(None, ge=0.0, le=1.0)
    source_url: Optional[str] = None

    # REQUIRED — so the raw module3 output remains valid
    # highlights: Optional[List[Highlight]] = None

    # REQUIRED — for user PDF offsets
    user_file_offsets: UserFileOffset = UserFileOffset()  # default empty offset





class BlockInput(BaseModel):
    block_id: str
    evidence: List[Module3Item]


class Module3Input(BaseModel):
    doc_id: str
    results: List[BlockInput]

    


# ---------------- CLEANED MODELS (used after clean_module3_output) ---------------- #

class CleanedSource(BaseModel):
    source_text: Optional[str] = None
    source_url: Optional[str] = None
    plagiarism_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    semantic_similarity: Optional[float] = Field(None, ge=0.0, le=1.0)
    score: float
    user_file_offsets: Optional[UserFileOffset] = None


class CleanedSentence(BaseModel):
    sentence: str
    sources: List[CleanedSource]
    occurrences: int
