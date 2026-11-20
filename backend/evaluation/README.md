# Requirement matching evaluation

The evaluator runs the same MiniLM retrieval and verification rules used by the API on 25 hand-labeled fictional cases. Each case contains one requirement and a short resume excerpt. Run `python -m app.evaluate` from `backend` with the local model available.

| Class | Precision | Recall | F1 | Support |
| --- | ---: | ---: | ---: | ---: |
| Supported | 1.000 | 0.900 | 0.947 | 10 |
| Partially Supported | 0.875 | 1.000 | 0.933 | 7 |
| Not Evidenced | 1.000 | 1.000 | 1.000 | 8 |
| Macro average | 0.958 | 0.967 | 0.960 | 25 |

Overall accuracy was **24/25 (96%)** on this set. One responsibility paraphrase was predicted Partially Supported instead of Supported.

| Expected / predicted | Supported | Partially Supported | Not Evidenced |
| --- | ---: | ---: | ---: |
| Supported | 9 | 1 | 0 |
| Partially Supported | 0 | 7 | 0 |
| Not Evidenced | 0 | 0 | 8 |

This is a small, synthetic English-language development set. Cases are short and intentionally probe known rules. The scores do not estimate performance on representative job postings, on multilingual resumes, or in a real ATS. Independent annotations and a held-out dataset are needed for a meaningful generalization estimate.

