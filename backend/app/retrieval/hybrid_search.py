from sqlalchemy.orm import Session
from app.db.models import DocumentChunk
from app.retrieval.vector_search import search_with_scores
from app.retrieval.keyword_search import bm25_search_with_scores
from app.retrieval.reranker import rerank, rerank_with_scores


def normalize_scores(scores: list[float]) -> list[float]:
    if not scores:
        return []
    min_score = min(scores)
    max_score = max(scores)
    if max_score == min_score:
        return [1.0 for _ in scores]  # avoid divide-by-zero if all scores are equal
    return [(s - min_score) / (max_score - min_score) for s in scores]


def hybrid_search(
    db: Session,
    query: str,
    top_k: int = 5,
    alpha: float = 0.7,
    candidate_pool_size: int = 20,
) -> list[DocumentChunk]:
    vector_results = search_with_scores(db, query, top_k=candidate_pool_size)
    bm25_results = bm25_search_with_scores(db, query, top_k=candidate_pool_size)

    vector_scores_raw = [score for _, score in vector_results]
    bm25_scores_raw = [score for _, score in bm25_results]

    vector_scores_norm = normalize_scores(vector_scores_raw)
    bm25_scores_norm = normalize_scores(bm25_scores_raw)

    # build chunk_id -> normalized score maps
    vector_score_map = {
        chunk.id: norm_score
        for (chunk, _), norm_score in zip(vector_results, vector_scores_norm)
    }
    bm25_score_map = {
        chunk.id: norm_score
        for (chunk, _), norm_score in zip(bm25_results, bm25_scores_norm)
    }

    # collect every chunk that appeared in EITHER pool
    all_chunks = {chunk.id: chunk for chunk, _ in vector_results}
    all_chunks.update({chunk.id: chunk for chunk, _ in bm25_results})

    combined_scores = []
    for chunk_id, chunk in all_chunks.items():
        v_score = vector_score_map.get(chunk_id, 0.0)
        b_score = bm25_score_map.get(chunk_id, 0.0)
        combined = alpha * v_score + (1 - alpha) * b_score
        combined_scores.append((chunk, combined))

    combined_scores.sort(key=lambda pair: pair[1], reverse=True)

    return [chunk for chunk, _ in combined_scores[:top_k]]


def hybrid_then_rerank(
    db: Session,
    query:str,
    top_k:int = 5,
    alpha: float = 0.7,
    candidate_pool_size: int = 20,
) -> list[DocumentChunk]:

    candidates = hybrid_search(
        db,query,top_k=candidate_pool_size, alpha=alpha, candidate_pool_size=candidate_pool_size
    )

    return rerank(query, candidates, top_k=top_k)


def hybrid_then_rerank_with_scores(
    db: Session,
    query:str,
    top_k: int = 5,
    alpha: float = 0.7,
    candidate_pool_size: int = 20
) -> list[tuple[DocumentChunk, float]]:

    candidates = hybrid_search(
        db,query,top_k=candidate_pool_size, alpha=alpha, candidate_pool_size=candidate_pool_size
    )

    return rerank_with_scores(query, candidates, top_k=top_k)