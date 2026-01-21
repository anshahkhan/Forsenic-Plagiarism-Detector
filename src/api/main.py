# src/api/main.py
from fastapi import FastAPI
from .ingestion_api import router as ingestion_router
from .similarity_api import router as similarity_router
from .forsenics_api import router as forsenics_router
from .pipeline_api import router as pipeline_router
from .JsonUI import router as JsonUI

from .newjson import router as Clean_router
app = FastAPI(title="DF Project - MVP")

# Include ingestion routes
app.include_router(ingestion_router)

# Include similarity routes
app.include_router(similarity_router)

app.include_router(forsenics_router)


app.include_router(pipeline_router)
app.include_router(Clean_router)
app.include_router(JsonUI)

@app.get("/")
def read_root():
    return {"message": "DF Project MVP is running!"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
