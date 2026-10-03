import json
import re
from app.generation.llm_client import generate

JUDGE_SYSTEM_PROMPT = """You are a strict fact-checker. You will be given a CONTEXT and an ANSWER.
Determine whether every claim in the ANSWER is directly supported by the CONTEXT.

Respond with ONLY a JSON object, no other text, in this exact shape:
{"faithful": true or false, "unsupported_claims": ["list", "of", "claims", "not", "supported", "by", "context"], "reasoning": "one sentence"}

If the answer correctly says it could not find information, that counts as faithful.
A claim counts as unsupported if it states a specific fact, number, or policy that does not appear in the context, even if it sounds plausible."""


def check_faithfulness(context: str, answer: str) -> dict:
    prompt = f"CONTEXT:\n{context}\n\nANSWER:\n{answer}\n\nJSON verdict:"
    raw = generate(prompt, system=JUDGE_SYSTEM_PROMPT)

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return {"faithful": None, "unsupported_claims": [], "reasoning": "judge did not return parseable JSON", "raw": raw}

    try:
        result = json.loads(match.group(0))
        result["raw"] = raw
        return result
    except json.JSONDecodeError:
        return {"faithful": None, "unsupported_claims": [], "reasoning": "judge returned malformed JSON", "raw": raw}