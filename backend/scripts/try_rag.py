import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.generation.llm_client import LLMError
from app.services.rag_service import answer_question

QUESTIONS = [
    "Can I get my money back?",
    "How do I unlock a customer's account after too many failed logins?",
    "What is the weather like today?",
    "Can I get a refund after 18 months?",
]


def main():
    db = SessionLocal()

    for question in QUESTIONS:
        print(f"\n=== {question}")
        try:
            result = answer_question(db, question)
        except LLMError as e:
            print(f"LLM error: {e}")
            continue

        print(f"\nANSWER:\n{result['answer']}")
        print("\nCITATIONS:")
        if result["citations"]:
            for c in result["citations"]:
                print(f"  [{c['id']}] {c['document_title']}, page {c['page']}")
        else:
            print("  (none)")
        if result["invalid_citation_ids"]:
            print(f"  ! invalid ids cited by the model: {result['invalid_citation_ids']}")

        t = result["timings"]
        print(
            f"\nretrieval {t['retrieval']:.1f}s | generation {t['generation']:.1f}s | "
            f"total {t['retrieval'] + t['generation']:.1f}s"
        )

    db.close()


if __name__ == "__main__":
    main()