# YesRole demo and viva guide

## Before the evaluation

Start both services using the [README](README.md). On a fresh machine, install dependencies and download MiniLM in advance. From `backend`, run `..\.venv\Scripts\python.exe -m app.demo_pdf` to create `.runtime/demo-resume.pdf`. Open [demo-job.txt](backend/evaluation/demo-job.txt) so you can paste the fictional job description. Run one analysis to warm the local model if you want to avoid the first-load delay during the presentation.

## Two-minute walkthrough

| Time | Show | Explain |
| --- | --- | --- |
| 0:00–0:20 | Dashboard → New Analysis. Upload the fictional PDF, paste the internship description, enter its title, and run analysis. | YesRole helps applicants see how their resume supports a specific role. The same pipeline handles user input and the built-in fictional demos. |
| 0:20–0:55 | Open the match report. Expand a supported Python requirement and the Docker gap. | MiniLM embeds job requirements and resume passages as vectors. Cosine similarity retrieves likely evidence. Rules check the required technology or credential before awarding full credit. |
| 0:55–1:25 | Show ATS Readability. Open Optimization Studio. Accept a grounded rewrite or manually edit one project line. Leave Docker unevidenced. | The ATS checks examine document readability. The editor proposes wording the applicant can review, reject or undo. |
| 1:25–2:00 | Reanalyze. Show scores, coverage changes, the diff, and remaining gaps. Download DOCX or PDF. | Scores can go up, go down or stay the same. Both versions use the same engine and job description. The export contains the edited draft. |

For a fast walkthrough without a file, use **Try Demo**. For a deliberately mismatched example, paste a fictional cafeteria budgeting resume with Excel and Power BI as the only skills and use the ML internship description. Compare the resulting gaps with the original demo.

## Embeddings and cosine similarity

An embedding maps text to numbers that capture aspects of meaning. MiniLM outputs one 384-dimensional vector per requirement or passage. The cosine is the dot product divided by the product of the vector lengths. YesRole normalizes vectors first, so it multiplies the vectors directly to get cosine similarities. This lets “questionnaire responses” and “survey responses” retrieve similar passages even when the words differ. It still takes a verification step to decide whether the passage demonstrates every part of the qualification.

## Ten viva questions

1. **What problem does YesRole solve?** It finds where a job seeker’s resume demonstrates specific requirements and where the resume could explain relevant experience more clearly.
2. **What is the model?** The pre-trained Sentence Transformers all-MiniLM-L6-v2 encoder. YesRole runs inference locally on the CPU, with no training step for the encoder.
3. **Why compare passages?** A single whole-document similarity cannot point to which line supports which requirement. Passage retrieval gives the applicant a quote to inspect.
4. **Why is semantic retrieval better than keyword-only matching?** It can find relevant evidence across paraphrases. Skill aliases such as k8s and Kubernetes give explicit evidence where exact terminology varies.
5. **How do you avoid confusing Docker with Python?** The explicit skill rule requires evidence for Docker. Cosine similarity can surface a passage, but cannot verify a missing named tool.
6. **How is the score calculated?** YesRole blends required and preferred coverage, semantic relevance, experience alignment, and evidence quality. Coverage credits are 1, 0.5, and 0. Effective weights are renormalized over applicable dimensions.
7. **What does ATS Readability mean?** It checks observable properties such as selectable text, recognizable headings and date patterns. The YesRole Match Score answers a separate question about role evidence.
8. **How is the system evaluated?** A small set of 25 labeled fictional cases exercises the real model. Precision measures how often a predicted label is correct, recall measures how often the pipeline finds that label, and F1 balances the two. The confusion matrix shows where labels were confused.
9. **How does YesRole apply Responsible AI?** It shows the source and reasoning, uses local inference, gives applicants control over every edit, and does not invent employment, skills or credentials. The score is a resume alignment heuristic.
10. **How could it use Azure later?** A consented version could use Azure Document Intelligence for layout extraction and Azure AI Search with a deployed embedding model for retrieval. The current app does not require Azure credentials.

