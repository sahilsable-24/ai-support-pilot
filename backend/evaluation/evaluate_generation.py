import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.db.session import SessionLocal
from app.db.models import Document
from app.services.rag_service import answer_question
from app.generation.faithfulness import check_faithfulness
from app.generation.citation_correctness import check_citation_correctness
from app.generation.prompts import build_context


def load_dataset(path: str) -> list[dict]:
    with open(path, "r") as f:
        return json.load(f)


def main():
    dataset = load_dataset("evaluation/dataset.json")
    db = SessionLocal()

    answerable = [q for q in dataset if q["expected_document_title"]]

    faithful_count = 0
    unfaithful_count = 0
    judge_failed_count = 0
    all_correctness_results = []

    for item in answerable:
        question = item["question"]
        result = answer_question(db, question)

        if result["insufficient_evidence"]:
            print(f"[SKIPPED - no evidence] '{question}'")
            continue

        doc_ids = {c.document_id for c in result["chunks"]}
        documents = db.scalars(select(Document).where(Document.id.in_(doc_ids))).all()
        real_titles = {d.id: d.title for d in documents}
        context = build_context(result["chunks"], real_titles)

        # --- faithfulness ---
        verdict = check_faithfulness(context, result["answer"])

        if verdict["faithful"] is None:
            judge_failed_count += 1
            status = "JUDGE FAILED"
        elif verdict["faithful"]:
            faithful_count += 1
            status = "FAITHFUL"
        else:
            unfaithful_count += 1
            status = "UNFAITHFUL"

        print(f"\n[{status}] '{question}'")
        if verdict["faithful"] is False:
            print(f"    unsupported: {verdict['unsupported_claims']}")
            print(f"    reasoning: {verdict['reasoning']}")

        # --- citation correctness ---
        correctness_results = check_citation_correctness(result["answer"], result["citations"])
        for cr in correctness_results:
            if cr["supported"] is False:
                print(f"    [CITATION ISSUE] [{cr['citation_id']}] does not support: \"{cr['sentence']}\"")
                print(f"        reasoning: {cr['reasoning']}")

        all_correctness_results.extend(correctness_results)

    scored = faithful_count + unfaithful_count
    faithfulness_rate = faithful_count / scored if scored else 0

    supported = sum(1 for r in all_correctness_results if r["supported"] is True)
    checked = sum(1 for r in all_correctness_results if r["supported"] is not None)
    correctness_rate = supported / checked if checked else 0

    print(f"\nFaithfulness: {faithful_count}/{scored} ({faithfulness_rate * 100:.1f}%)")
    print(f"Judge call failures (faithfulness): {judge_failed_count}")
    print(f"Citation correctness: {supported}/{checked} ({correctness_rate * 100:.1f}%)")

    db.close()


if __name__ == "__main__":
    main()