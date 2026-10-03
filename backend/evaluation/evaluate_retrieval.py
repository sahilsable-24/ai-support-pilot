import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.db.models import Document
from app.retrieval.vector_search import search as vector_search
from app.retrieval.keyword_search import bm25_search
from app.retrieval.hybrid_search import hybrid_search, hybrid_then_rerank

TOP_K = 5


def load_dataset(path: str) -> list[dict]:
    with open(path, "r") as f:
        return json.load(f)


def get_document_id_by_title(db, title: str):
    doc = db.query(Document).filter(Document.title == title).first()
    return doc.id if doc else None


def evaluate(db, dataset, search_fn, label: str):
    print(f"\n=== {label} ===")
    hits = 0
    total_precision = 0.0
    total_reciprocal_rank = 0.0
    scored_count = 0

    for item in dataset:
        question = item["question"]
        expected_title = item["expected_document_title"]

        results = search_fn(db, question, top_k=TOP_K)
        retrieved_doc_ids = [str(chunk.document_id) for chunk in results]

        if expected_title is None:
            print(f"[UNSCORED] '{question}'")
            if results:
                print(f"    top result: {results[0].content[:80]}...")
            continue

        expected_id = get_document_id_by_title(db, expected_title)
        expected_id_str = str(expected_id) if expected_id else None

        hit = expected_id_str is not None and expected_id_str in retrieved_doc_ids
        relevant_count = sum(1 for doc_id in retrieved_doc_ids if doc_id == expected_id_str)
        precision = relevant_count / TOP_K

        first_relevant_rank = None
        for rank, doc_id in enumerate(retrieved_doc_ids, start=1):
            if doc_id == expected_id_str:
                first_relevant_rank = rank
                break
        reciprocal_rank = 1 / first_relevant_rank if first_relevant_rank else 0

        status = "HIT " if hit else "MISS"
        print(f"[{status}] '{question}'  (precision={precision:.2f}, rr={reciprocal_rank:.2f})")
        if results:
            print(f"    top result: {results[0].content[:80]}...")

        if hit:
            hits += 1
        total_precision += precision
        total_reciprocal_rank += reciprocal_rank
        scored_count += 1

    recall = hits / scored_count if scored_count else 0
    avg_precision = total_precision / scored_count if scored_count else 0
    mrr = total_reciprocal_rank / scored_count if scored_count else 0

    print(f"\nRecall@{TOP_K}: {hits}/{scored_count} ({recall * 100:.1f}%)")
    print(f"Precision@{TOP_K}: {avg_precision:.2f}")
    print(f"MRR: {mrr:.2f}")


def main():
    dataset = load_dataset("evaluation/dataset.json")
    db = SessionLocal()

    evaluate(db, dataset, vector_search, "Vector Search")
    evaluate(db, dataset, bm25_search, "BM25 Search")
    evaluate(db, dataset, lambda db, q, top_k: hybrid_search(db, q, top_k, alpha=0.7), "Hybrid (alpha=0.7)")
    evaluate(db, dataset, hybrid_then_rerank, "Hybrid + Rerank")

    db.close()


if __name__ == "__main__":
    main()