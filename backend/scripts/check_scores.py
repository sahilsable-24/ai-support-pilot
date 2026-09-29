import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.retrieval.hybrid_search import hybrid_then_rerank_with_scores

ANSWERABLE = [
    "Can I get my money back?",
    "How do I unlock a customer's account after too many failed logins?",
    "How do I upgrade my subscription plan?",
    "Can I download a copy of my data before closing my account?",
]

UNANSWERABLE = [
    "What is the weather like today?",
    "Do you offer discounts for annual plans?",
    "Is my data encrypted?",
    "What is your phone number for billing support?",
]


def main():
    db = SessionLocal()

    print("=== Answerable questions ===")
    for q in ANSWERABLE:
        scored = hybrid_then_rerank_with_scores(db, q)
        top_score = scored[0][1] if scored else None
        print(f"{top_score:.3f}  {q}")

    print("\n=== Unanswerable questions ===")
    for q in UNANSWERABLE:
        scored = hybrid_then_rerank_with_scores(db, q)
        top_score = scored[0][1] if scored else None
        print(f"{top_score:.3f}  {q}")

    db.close()


if __name__ == "__main__":
    main()