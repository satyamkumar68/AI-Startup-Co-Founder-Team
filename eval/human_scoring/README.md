# Human Scoring Workflow

This directory contains the tools and templates for conducting blinded, randomized human peer reviews of venture deliverables.

## Scientific Evaluation Protocol
To prevent confirmation bias:
1. Deliverables from all 3 modes (`single_agent`, `multi_no_debate`, `multi_debate`) are given random anonymized IDs (`BLIND-XXXXXX`).
2. Mode identities are stripped from the evaluation sheet and stored securely in `.key_mapping.json`.
3. Reviewers evaluate deliverables across the standardized 5-dimension rubric (1.0 – 5.0 scale):
   - **Market Realism**: Sanity of TAM/SAM math and source citations.
   - **Internal Consistency**: Alignment between PRD personas, user stories, and tech stack.
   - **Architecture & Cost Feasibility**: Grounded cloud cost breakdown and infrastructure plausibility.
   - **Specificity**: Concrete user stories and KPIs vs. generic buzzwords.
   - **Risk Awareness**: Technical, security, and market threat modeling.

## How to Run Human Evaluation
1. Generate the blinded evaluation sheet:
   ```bash
   python -m eval.generate_human_csv
   ```
2. Have human reviewers fill in scores in `blinded_scoring_sheet.csv`.
3. Ingest and merge scores into the benchmark report:
   ```bash
   python -m eval.merge_human
   ```
   *Note: If no scores are filled in, the system reports status as `not_measured` without inventing synthetic numbers.*
