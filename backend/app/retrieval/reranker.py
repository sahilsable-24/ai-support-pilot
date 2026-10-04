
from app.db.models import DocumentChunk

_reranker = None

def get_reranker():
    global _reranker
    if _reranker is None:
        from sentence_transformers import CrossEncoder
        _reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _reranker


def rerank_with_scores(query:str, chunks:list[DocumentChunk], top_k: int=5) -> list[tuple[DocumentChunk, float]]:

    if not chunks:
        return []

    reranker = get_reranker()

    pairs = [(query,chunk.content) for chunk in chunks]
    scores = reranker.predict(pairs)

    scored_chunks = list(zip(chunks,scores))

    scored_chunks.sort(key=lambda pair: pair[1], reverse=True)

    return scored_chunks[:top_k]


def rerank(query:str, chunks: list[DocumentChunk], top_k: int=5) -> list[DocumentChunk]:

    scored = rerank_with_scores(query,chunks,top_k)
    return [chunk for chunk,score in scored]