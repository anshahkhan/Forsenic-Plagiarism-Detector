# src/api/main.py
from fastapi import FastAPI
from src.api.ingestion_api import router as ingestion_router
from src.api.similarity_api import router as similarity_router
from src.api.forsenics_api import router as forsenics_router
<<<<<<< HEAD
from src.api.pipeline_api import router as pipeline_router

=======
from src.api.newjson import router as Clean_router
>>>>>>> 20b6e8ab029549b1c5c3a512772d531f8ea99a13
app = FastAPI(title="DF Project - MVP")

# Include ingestion routes
app.include_router(ingestion_router)

# Include similarity routes
app.include_router(similarity_router)

app.include_router(forsenics_router)

<<<<<<< HEAD

app.include_router(pipeline_router)
=======
app.include_router(Clean_router)
>>>>>>> 20b6e8ab029549b1c5c3a512772d531f8ea99a13

@app.get("/")
def read_root():
    return {"message": "DF Project MVP is running!"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
