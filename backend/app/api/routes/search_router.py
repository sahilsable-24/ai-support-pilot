from fastapi import APIRouter,Depends
from app.retrieval.vector_search import search
from sqlalchemy.orm import Session
from app.db.session import get_db



router = APIRouter(prefix="/search", tags=["search"])


@router.post("")
def search_chunks(query:str, top_k:int = 5, db: Session=Depends(get_db)):

    results = search(db,query,top_k)

    return [
        {
            "chunk_id": str(chunk.id),
            "document_id": str(chunk.document_id),
            "page": chunk.page,
            "content": chunk.content
        }
        for chunk in results
    ]