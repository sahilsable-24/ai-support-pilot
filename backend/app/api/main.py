from fastapi import FastAPI, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db
from app.api.routes.document_router import router as document_router
from app.api.routes.search_router import router as search_router
import logging

logging.basicConfig(level=logging.INFO)

app = FastAPI()

@app.get("/health")
def get_health():
    return {"status":"ok"}

@app.get("/db-check")
def get_db_check(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT 1")).scalar()

    if result != 1:
        raise HTTPException(status_code=500, detail="something went wrong")
    return {"database": "connected"} 

app.include_router(document_router)
app.include_router(search_router)