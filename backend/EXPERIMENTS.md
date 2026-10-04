# SupportPilot — Retrieval & Generation Experiment Log

## Setup

Dataset: `evaluation/dataset.json` — 18 scored questions (originally 10, expanded Day 24)
across 3 source documents (support policy PDF, employee onboarding guide, product feature
guide), plus 2 deliberately unanswerable distractor questions and 1 off-topic control
question. The legacy Lorem Ipsum test PDF from early ingestion testing was removed before
the expanded dataset was built, so all current numbers reflect only intentional content.

## Retrieval

| Configuration | Recall@5 | Precision@5 | MRR | Notes |
|---|---|---|---|---|
| Vector search (baseline) | 100% | 0.49 | 0.97 | One near-miss: top result for "Can a Viewer change billing settings?" was a topically adjacent but incorrect chunk, landing the right answer at rank 2 |
| BM25 (keyword) | 94.1% | 0.48 | 0.80 | Missed "When will my order ship?" entirely — zero literal word overlap between the question and the document's actual phrasing |
| Hybrid, alpha=0.5 | 100% | 0.58 | 0.97 | Recovered BM25's miss, but dropped the recovered answer to rank 3 on that question |
| Hybrid, alpha=0.7 | 100% | 0.58 | 0.97 | Tuned weighting toward vector search; precision held, did not fully resolve the alpha=0.5 ranking cost on the harder 18-question set |
| **Hybrid + Rerank** | **100%** | **0.55** | **1.00** | Best MRR of any configuration; cross-encoder reranking corrected the Viewer/billing near-miss that vector search alone got wrong |

### Key findings

**BM25 and vector search fail in opposite, predictable ways.** BM25 only matches literal
words, so it fails whenever a question paraphrases the source text ("money back" vs.
"refund", "order ship" vs. "digital product, no physical shipping"). Vector search
compares meaning, not exact wording, so it handled every paraphrased question correctly,
its only miss was a case where two *topically similar* chunks (billing and permissions)
both scored well and the wrong one edged out the right one for the top spot.

**Alpha controls how much each method's score contributes to the final ranking, not the
metrics directly.** Moving alpha from 0.5 to 0.7 shifts weight toward vector search's
scores and away from BM25's, in the score-combination formula. On the original 10-question
dataset this fully resolved a ranking cost (MRR returned to 1.00). On the expanded
18-question dataset, alpha alone wasn't enough to recover MRR to 1.00, that gap was closed
instead by reranking.

**Reranking's value showed up specifically in ranking quality (MRR), not in whether the
right document was found at all (Recall).** Recall was already 100% by the hybrid stage,
there was no room left for reranking to improve it. What reranking fixed was a case where
the correct document was retrieved but not ranked first, the cross-encoder's direct
query-chunk scoring resolved that near-miss where score-based hybrid combination alone did
not.

**Still open**: precision dropped from 0.80 (original 10-question, 2-document set) to 0.55
(current 18-question, 3-document set) across every configuration. This is expected, more
documents and more topically-overlapping questions mean more plausible near-misses compete
for the top-5 slots, it is not a regression in the underlying retrieval methods. Precision
has not been re-measured since the Lorem Ipsum document was removed from the earlier
smaller-dataset numbers, so the 0.80 and 0.55 figures aren't a perfectly clean comparison,
noted here rather than implied as directly comparable.

## Generation

Measured using LLM-as-judge (Groq, `openai/gpt-oss-120b`) against the 16 answerable
questions that received a generated answer (2 of the 18 correctly triggered the
evidence-sufficiency check and were never sent to the LLM).

| Metric | Result |
|---|---|
| Faithfulness | 14/17 (82.4%) on most recent run; 15/17 (88.2%) on an earlier run — see note below |
| Citation correctness | Implemented; last measured number (55%) is known unreliable, see note below |
| Judge call failures | 0 |

### Key findings

**Faithfulness catches claims that are technically cited but not actually stated in the
source.** Two confirmed cases: an answer described a specific submission mechanism for
account deletion that the source document never specified, and an answer turned the
source's silence on other user roles into an implied negative claim ("2FA is required only
for Admins" was read as "not required for anyone else," which the document never actually
says). Both were correctly caught by the faithfulness judge and would not have been caught
by citation validation alone, since both citations pointed at real, retrieved chunks.

**Faithfulness and citation validity are different guarantees.** A citation can correctly
point to a real chunk the model actually saw, and the claim next to it can still be false
or unsupported. Day 18's citation validation stops the model from inventing a source
entirely; faithfulness checking is the separate, necessary check for whether the cited
source actually backs up the specific claim.

**The faithfulness rate varied between two runs on the same dataset (88.2% vs. 82.4%)
using the same system, with no code change between them.** Likely LLM sampling variance,
expected and not investigated further given time constraints, but worth noting as a
limitation: a single run's percentage should be read as directional, not as a precise,
stable figure, without averaging multiple runs.

**Citation correctness, as implemented, has a known bug and the 55% figure should not be
cited.** The judge model was found to return `supported: false` paired with the
`"no claim to check"` reasoning string, which the prompt defines as the justification for
a *true* verdict, an internal contradiction in the judge's own output. The system prompt
was tightened to explicitly forbid that pairing, but the fix has not yet been re-run
against the dataset to produce a corrected number.

## What's next

- Re-run citation correctness after the judge-prompt fix to get a trustworthy number
- Average faithfulness over multiple runs rather than reporting a single pass
- Re-measure retrieval precision on the current dataset+document set for a clean
  before/after comparison once the Lorem Ipsum removal and dataset expansion are both
  accounted for in the same run