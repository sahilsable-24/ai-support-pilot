from app.db.models import Message
from app.generation.llm_client import generate


REWRITE_SYSTEM_PROMPT = """You rewrite a follow-up question into a standalone question, using the conversation so far for context.

Rules:
1. Output ONLY the rewritten question. No explanation, no answer, no extra text.
2. Replace pronouns and vague references ("it", "that", "the email") with what they actually refer to, based on the conversation.
3. If the new question is already standalone and doesn't depend on the conversation, output it unchanged.
4. Do not answer the question. Only rewrite it."""


def format_history(messages: list[Message], max_turns: int=4) -> str:

    recent = messages[-max_turns:]
    lines = [f"{m.role}: {m.content}" for m in recent]
    return "\n".join(lines)

def rewrite_query(history: list[Message], question:str) -> str:
    if not history:
        return question

    transcript = format_history(history)
    prompt = f"Conversation so far:\n{transcript}\n\nNew question: {question}\n\nStandalone question:"

    rewritten = generate(prompt, system=REWRITE_SYSTEM_PROMPT)
    return rewritten.strip()