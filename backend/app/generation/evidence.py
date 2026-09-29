from app.db.models import DocumentChunk


def has_sufficient_evidence(
    scored_chunks: list[tuple[DocumentChunk,float]],
    threshold: float
) -> bool:

    if not scored_chunks:
        return False
    top_score = scored_chunks[0][1]
    return top_score >= threshold