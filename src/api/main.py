# src/api/main.py
from fastapi import FastAPI
from src.api.ingestion_api import router as ingestion_router
from src.api.similarity_api import router as similarity_router
from src.api.forsenics_api import router as forsenics_router

app = FastAPI(title="DF Project - MVP")

# Include ingestion routes
app.include_router(ingestion_router)

# Include similarity routes
app.include_router(similarity_router)

app.include_router(forsenics_router)

@app.get("/")
def read_root():
    return {"message": "DF Project MVP is running!"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
