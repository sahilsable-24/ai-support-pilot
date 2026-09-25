import faiss 
import uuid 
from sqlalchemy.orm import Session
import numpy as np
from app.db.models import DocumentChunk
from sqlalchemy import select
from app.embeddings.embedder import get_model



def build_index(db:Session) -> tuple[faiss.Index,list[uuid.UUID]]:
    chunks = db.scalars(
        select(DocumentChunk).where(DocumentChunk.embedding.is_not(None))
    ).all()

    if not chunks:
        raise ValueError("No embedded chunks available to search")

    embeddings = np.array([chunk.embedding for chunk in chunks], dtype="float32")

    faiss.normalize_L2(embeddings)

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    chunk_ids = [chunk.id for chunk in chunks]

    return index, chunk_ids 


def search(db:Session, query: str, top_k: int = 5) -> list[DocumentChunk]:

    index,chunk_ids = build_index(db)

    model = get_model()
    query_vector = model.encode([query], normalize_embeddings=True)
    query_vector = np.array(query_vector,dtype="float32")

    scores, indices = index.search(query_vector,top_k)

    result_ids = [chunk_ids[i] for i in indices[0] if i != -1]

    chunks = db.scalars(
        select(DocumentChunk).where(DocumentChunk.id.in_(result_ids))
    ).all()

    chunks_by_id = {chunk.id:chunk for chunk in chunks}

    return [chunks_by_id[cid] for cid in result_ids if cid in chunks_by_id]