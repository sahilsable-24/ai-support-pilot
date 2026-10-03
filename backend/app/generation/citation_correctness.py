import re
import json
from app.generation.llm_client import generate

JUDGE_SYSTEM_PROMPT = """You check whether a single sentence is supported by a single piece of evidence.

Respond with ONLY a JSON object, no other text:
{"supported": true or false, "reasoning": "one short sentence"}

"supported" is true only if the evidence directly backs up what the sentence claims. A sentence that says "I could not find this" with evidence attached counts as not applicable; respond {"supported": true, "reasoning": "no claim to check"}.
Never use "no claim to check" as the reasoning when supported is false. If supported is false, state specifically what the evidence is missing."""


def split_sentences(answer: str) -> list[str]:
    raw = re.split(r"(?<=[.!?])\s+", answer.strip())
    return [s for s in raw if s.strip()]


def extract_ids_from_sentence(sentence: str) -> list[int]:
    ids = []
    for match in re.finditer(r"\[(\d+(?:\s*,\s*\d+)*)\]", sentence):
        for part in match.group(1).split(","):
            ids.append(int(part.strip()))
    return ids


def check_sentence_support(sentence: str, evidence_text: str) -> dict:
    prompt = f"EVIDENCE:\n{evidence_text}\n\nSENTENCE:\n{sentence}\n\nJSON verdict:"
    raw = generate(prompt, system=JUDGE_SYSTEM_PROMPT)

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return {"supported": None, "reasoning": "judge did not return parseable JSON"}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {"supported": None, "reasoning": "judge returned malformed JSON"}


def check_citation_correctness(answer: str, citations: list[dict]) -> list[dict]:
    citations_by_id = {c["id"]: c for c in citations}
    results = []

    for sentence in split_sentences(answer):
        cited_ids = extract_ids_from_sentence(sentence)
        if not cited_ids:
            continue

        for cid in cited_ids:
            citation = citations_by_id.get(cid)
            if citation is None:
                continue

            verdict = check_sentence_support(sentence, citation["snippet"])
            results.append({
                "sentence": sentence,
                "citation_id": cid,
                "document": citation["document_title"],
                "supported": verdict["supported"],
                "reasoning": verdict["reasoning"],
            })

    return results