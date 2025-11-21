# src/models/ingestion_models.py
from pydantic import BaseModel, HttpUrl
from typing import Optional

class URLInput(BaseModel):
    url: HttpUrl

class UploadResponse(BaseModel):
    status: str
    file_id: str
    filename: str
    path: Optional[str]
