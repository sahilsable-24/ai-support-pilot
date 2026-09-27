# SupportPilot — Retrieval Experiment Log

Dataset: `evaluation/dataset.json` — 9 scored questions, 1 unscored (deliberately unanswerable), across 3 documents (support policy PDF, employee onboarding guide, and a legacy test PDF from early ingestion testing).

| Configuration | Recall@5 | Precision@5 | MRR  | Notes |
|---|---|---|---|---|
| Vector search (baseline) | 100% | 0.67 | 1.00 | Strong baseline; perfect ranking on every scored question |
| BM25 (keyword) | 88.9% | 0.60 | 0.76 | Missed one paraphrased question entirely ("order ship" vs. document's actual wording) |
| Hybrid, alpha=0.5 | 100% | 0.73 | 0.93 | Recovered BM25's miss into a hit, but the correct answer dropped to rank 3 on that question |
| Hybrid, alpha=0.7 | 100% | 0.69 | 1.00 | Best overall configuration tested — matches or beats vector search on every metric |

## Key Findings

- BM25 failed on the 'order ship' question because it only matches literal words, and the question's wording didn't overlap with the document's actual phrasing. Vector search succeeded because it compares meaning, not exact words, so it recognized the question and the document's answer were related even with different vocabulary.
- Alpha=0.7 gave more weight to vector search's scores and less to BM25's scores in the combined ranking. Since BM25 was actively wrong on the 'order ship' question (ranking the wrong document highly), reducing its influence let vector search's correct ranking dominate again — which is why MRR went back up to 1.00, while hybrid still kept a slight precision edge over vector alone.

## Next Steps
- Test reranking on top of the alpha=0.7 hybrid configuration (Day 15)