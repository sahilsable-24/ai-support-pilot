import time
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models import Document
from app.generation.prompts import SYSTEM_PROMPT,build_context,build_user_prompt
from app.generation.llm_client import generate
from app.retrieval.hybrid_search import hybrid_then_rerank


def answer_question(db:Session, question:str, top_k:int=5) -> dict:
    start = time.perf_counter()
    chunks = hybrid_then_rerank(db,question,top_k=top_k)
    reterival_done = time.perf_counter()

    doc_ids = {chunk.document_id for chunk in chunks}
    documents = db.scalars(select(Document).where(Document.id.in_(doc_ids))).all()
    titles = {doc.id:doc.title for doc in documents}

    context = build_context(chunks,titles)
    prompt = build_user_prompt(question,context)

    generation_start = time.perf_counter()
    answer = generate(prompt, system=SYSTEM_PROMPT)
    generation_done = time.perf_counter()

    return {
        "answer": answer,
        "chunks": chunks,
        "timings": {
            "retrieval": reterival_done - start,
            "generation": generation_done - generation_start
        }
    }