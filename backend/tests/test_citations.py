import uuid
from app.db.models import DocumentChunk
from app.generation.citations import extract_citation_ids, build_citations

DOC_ID = uuid.uuid4()
TITLES = {DOC_ID: "refund_policy.pdf"}


def make_chunk(page: int, content: str) -> DocumentChunk:
    return DocumentChunk(
        id=uuid.uuid4(),
        document_id=DOC_ID,
        page=page,
        chunk_index=0,
        content=content,
    )


def test_extract_ids_keeps_order_and_removes_duplicates():
    assert extract_citation_ids("A [2]. B [1]. C [2].") == [2, 1]


def test_extract_ids_handles_commas_and_adjacent_markers():
    assert extract_citation_ids("A [1, 3]. B [2][4].") == [1, 3, 2, 4]


def test_valid_id_resolves_from_chunk_metadata():
    chunks = [make_chunk(1, "first chunk text"), make_chunk(4, "second chunk text")]
    citations, invalid = build_citations("Some claim [2].", chunks, TITLES)

    assert invalid == []
    assert citations[0]["page"] == 4
    assert citations[0]["document_title"] == "refund_policy.pdf"
    assert citations[0]["chunk_id"] == str(chunks[1].id)


def test_out_of_range_ids_are_rejected_and_not_resolved():
    chunks = [make_chunk(1, "only chunk")]
    citations, invalid = build_citations("Claim [9]. Other [0].", chunks, TITLES)

    assert citations == []
    assert invalid == [9, 0]


def test_source_names_written_by_the_model_are_ignored():
    chunks = [make_chunk(2, "real content")]
    answer = "Per Secret Handbook, page 7 [1]."
    citations, _ = build_citations(answer, chunks, TITLES)

    assert citations[0]["document_title"] == "refund_policy.pdf"
    assert citations[0]["page"] == 2


def test_answer_without_citations_returns_empty_lists():
    citations, invalid = build_citations("I could not find that.", [], TITLES)
    assert citations == [] and invalid == []