import json 
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.db.models import Document
from app.retrieval.vector_search import search

TOP_K = 5

def load_dataset(path:str) -> list[dict]:
    with open(path,"r") as f:
        return json.load(f)

def get_document_id_by_title(db,title:str):
    doc = db.query(Document).filter(Document.title == title).first()
    return doc.id if doc else None

def evaluate():
    dataset = load_dataset("evaluation/dataset.json")
    db = SessionLocal()

    hits = 0
    total = len(dataset)

    for item in dataset:
        question = item['question']
        expected_title = item["expected_document_title"]

        results = search(db,question,top_k=TOP_K)
        retrieved_doc_ids = [str(chunk.document_id) for chunk in results]

        if expected_title is None:
            print(f"[unscored] '{question}'")
            print(f"   top result: {results[0].content[:80] if results else 'none'}...")

            continue

        expected_id = get_document_id_by_title(db,expected_title)
        hit = expected_id is not None and str(expected_id) in retrieved_doc_ids

        status = "HIT " if hit else "MISS"
        print(f"[{status}] '{question}'")

        if results:
            print(f" top result: {results[0].content[:80]}...")

        if hit:
            hits +=1

    scored_total = total - sum(1 for i in dataset if i["expected_document_title"] is None)

    recall = hits / scored_total if scored_total else 0

    print(f"\nRecall@{TOP_K}: {hits}/{scored_total} ({recall * 100:.1f}%)")

    db.close()


if __name__ == "__main__":
    evaluate()