import uuid
from rank_bm25 import BM25Okapi
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.models import DocumentChunk


def tokenize(text:str) -> list[str]:
    return text.lower().split()

def build_bm25_index(db:Session) -> tuple[BM25Okapi, list[uuid.UUID]]:
    chunks = db.scalars(select(DocumentChunk)).all()

    if not chunks:
        raise ValueError("No chunks available to search")

    tokenized_corpus = [tokenize(chunk.content) for chunk in chunks]
    bm25 = BM25Okapi(tokenized_corpus)

    chunk_ids = [chunk.id for chunk in chunks]

    return bm25, chunk_ids


def bm25_search(db:Session, query: str, top_k: int=5) -> list[DocumentChunk]:

    bm25, chunk_ids = build_bm25_index(db)

    tokenized_query = tokenize(query)
    scores = bm25.get_scores(tokenized_query)

    #pairing each scores with the chunk_ids
    scored = list(zip(chunk_ids,scores))

    scored.sort(key=lambda pair: pair[1], reverse=True)
    top_results = scored[:top_k]

    result_ids = [chunk_id for chunk_id,score in top_results]

    chunks = db.scalars(
        select(DocumentChunk).where(DocumentChunk.id.in_(result_ids))
    ).all()

    chunks_by_id = {chunk.id:chunk for chunk in chunks}

    return [chunks_by_id[cid] for cid in result_ids if cid in chunks_by_id]


def bm25_search_with_scores(db: Session, query: str, top_k: int = 20) -> list[tuple[DocumentChunk, float]]:
    bm25, chunk_ids = build_bm25_index(db)

    tokenized_query = tokenize(query)
    scores = bm25.get_scores(tokenized_query)

    scored = list(zip(chunk_ids, scores))
    scored.sort(key=lambda pair: pair[1], reverse=True)
    top_results = scored[:top_k]

    result_ids = [chunk_id for chunk_id, _ in top_results]
    chunks = db.scalars(
        select(DocumentChunk).where(DocumentChunk.id.in_(result_ids))
    ).all()
    chunks_by_id = {chunk.id: chunk for chunk in chunks}

    return [
        (chunks_by_id[chunk_id], score)
        for chunk_id, score in top_results
        if chunk_id in chunks_by_id
    ]