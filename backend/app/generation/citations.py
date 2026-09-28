import re
from app.db.models import DocumentChunk

# matches [1], and also [1, 2] since small models often write it that way
CITATION_PATTERN = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")


def extract_citation_ids(answer: str) -> list[int]:
    ids: list[int] = []
    for match in CITATION_PATTERN.finditer(answer):
        for part in match.group(1).split(","):
            citation_id = int(part.strip())
            if citation_id not in ids:
                ids.append(citation_id)
    return ids


def build_citations(
    answer: str,
    chunks: list[DocumentChunk],
    titles: dict,
    snippet_length: int = 150,
) -> tuple[list[dict], list[int]]:
    citations = []
    invalid_ids = []

    for citation_id in extract_citation_ids(answer):
        if 1 <= citation_id <= len(chunks):
            chunk = chunks[citation_id - 1]
            citations.append({
                "id": citation_id,
                "document_title": titles.get(chunk.document_id, "Unknown document"),
                "page": chunk.page,
                "chunk_id": str(chunk.id),
                "snippet": chunk.content[:snippet_length],
            })
        else:
            invalid_ids.append(citation_id)

    return citations, invalid_ids