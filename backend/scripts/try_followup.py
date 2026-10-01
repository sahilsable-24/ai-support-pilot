# scripts/try_followup.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.services.rag_service import answer_question

db = SessionLocal()

r1 = answer_question(db, "How do I unlock a customer's account after too many failed logins?")
print("TURN 1 ANSWER:", r1["answer"])

r2 = answer_question(db, "What if they say they never got the email?", conversation_id=r1["conversation_id"])
print("\nTURN 2 ANSWER:", r2["answer"])

db.close()