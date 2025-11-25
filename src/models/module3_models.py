# src/models/module3_models.py
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl


class Highlight(BaseModel):
    start: int
    end: int
    type: Optional[str] = None


class UserFileOffset(BaseModel):
    start: int
    end: int


class Module3Item(BaseModel):
    """
    Model for one evidence item from Module 3 output.
    Fields match the example you provided. Add/adjust if your module3 output differs.
    """
    sentence: str
    type: Optional[str] = None
    source_text: Optional[str] = None
    plagiarism_score: Optional[float] = Field(0.0, ge=0.0, le=1.0)
    semantic_similarity: Optional[float] = Field(0.0, ge=0.0, le=1.0)
    source_url: Optional[str] = None
    # highlights: Optional[List[Highlight]] = []
    user_file_offsets: Optional[UserFileOffset] = None



class CleanedSource(BaseModel):
    source_text: Optional[str] = None
    source_url: Optional[str] = None
    plagiarism_score: Optional[float] = Field(0.0, ge=0.0, le=1.0)
    semantic_similarity: Optional[float] = Field(0.0, ge=0.0, le=1.0)
    score: float  # (semantic + plagiarism)/2 rounded
    highlights: Optional[List[Highlight]] = []


class CleanedSentence(BaseModel):
    sentence: str
    sources: List[CleanedSource]
    aggregated_score: float  # average of the selected sources' score
    occurrences: int
