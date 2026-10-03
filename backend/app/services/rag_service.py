import time
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models import Document
from app.generation.prompts import SYSTEM_PROMPT,build_context,build_user_prompt
from app.generation.llm_client import generate
from app.retrieval.hybrid_search import hybrid_then_rerank, hybrid_then_rerank_with_scores
import logging
from app.generation.citations import build_citations
from app.core.config import settings
from app.generation.evidence import has_sufficient_evidence
import uuid
from app.services.conversation_service import create_conversation,add_message, get_messages
from app.generation.query_rewriting import rewrite_query
logger = logging.getLogger(__name__)

NO_EVIDENCE_MESSAGE = (
    "I couldn't find enough information in the knowledge base to answer this. "
    "Recommended action: escalate to the relevant team."
)


def answer_question(db: Session, question: str, conversation_id: uuid.UUID | None = None, top_k: int = 5) -> dict:

    if conversation_id is None:
        conversation = create_conversation(db)
        conversation_id = conversation.id
        history = []
    else:
        history = get_messages(db,conversation_id)

    retrieval_query = rewrite_query(history,question) if history else question

    add_message(db,conversation_id,"user",question)

    start = time.perf_counter()
    scored_chunks = hybrid_then_rerank_with_scores(db, retrieval_query, top_k=top_k)
    retrieval_done = time.perf_counter()

    if not has_sufficient_evidence(scored_chunks, settings.evidence_threshold):
        assistant_message = add_message(db,conversation_id,"assistant", NO_EVIDENCE_MESSAGE)
        return {
            "answer": NO_EVIDENCE_MESSAGE,
            "conversation_id": conversation_id,
            "message_id": assistant_message.id,
            "chunks": [],
            "citations": [],
            "invalid_citation_ids": [],
            "insufficient_evidence": True,
            "timings": {
                "retrieval": retrieval_done - start,
                "generation": 0.0,
            },
        }

    chunks = [chunk for chunk, score in scored_chunks]

    doc_ids = {chunk.document_id for chunk in chunks}
    documents = db.scalars(select(Document).where(Document.id.in_(doc_ids))).all()
    titles = {doc.id: doc.title for doc in documents}

    context = build_context(chunks, titles)
    prompt = build_user_prompt(retrieval_query, context)

    generation_start = time.perf_counter()
    answer = generate(prompt, system=SYSTEM_PROMPT)
    generation_done = time.perf_counter()

    citations, invalid_ids = build_citations(answer, chunks, titles)
    if invalid_ids:
        logger.warning(f"Model cited ids that were not in the context: {invalid_ids}")

    assistant_message = add_message(db,conversation_id,"assistant",answer,citations=citations or None)

    return {
        "answer": answer,
        "conversation_id": conversation_id,
        "message_id": assistant_message.id,
        "chunks": chunks,
        "citations": citations,
        "invalid_citation_ids": invalid_ids,
        "insufficient_evidence": False,
        "timings": {
            "retrieval": retrieval_done - start,
            "generation": generation_done - generation_start,
        },
    }