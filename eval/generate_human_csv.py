import os
import csv
import json
import random
import uuid
from typing import List, Dict, Any


def generate_blinded_template(
    runs_data: List[Dict[str, Any]],
    output_csv_path: str = "eval/human_scoring/blinded_scoring_sheet.csv",
    key_mapping_path: str = "eval/human_scoring/.key_mapping.json"
):
    """Generate a randomized, blinded CSV sheet for human peer review.
    
    Hides the generation mode (single_agent, multi_no_debate, multi_debate)
    to eliminate confirmation bias.
    """
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    
    blinded_rows = []
    key_mapping = {}

    for run in runs_data:
        blind_id = f"BLIND-{uuid.uuid4().hex[:6].upper()}"
        key_mapping[blind_id] = {
            "mode": run.get("mode", "unknown"),
            "idea_id": run.get("idea_id", "unknown"),
            "idea_title": run.get("title", "")
        }

        blinded_rows.append({
            "blind_id": blind_id,
            "idea_id": run.get("idea_id", ""),
            "idea_title": run.get("title", ""),
            "deliverables_link": run.get("deliverables_path", ""),
            "market_realism_1_to_5": "",
            "internal_consistency_1_to_5": "",
            "feasibility_cost_1_to_5": "",
            "specificity_1_to_5": "",
            "risk_awareness_1_to_5": "",
            "reviewer_notes": ""
        })

    # Shuffle rows to avoid consecutive comparisons
    random.shuffle(blinded_rows)

    fieldnames = [
        "blind_id", "idea_id", "idea_title", "deliverables_link",
        "market_realism_1_to_5", "internal_consistency_1_to_5",
        "feasibility_cost_1_to_5", "specificity_1_to_5",
        "risk_awareness_1_to_5", "reviewer_notes"
    ]

    with open(output_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(blinded_rows)

    with open(key_mapping_path, "w", encoding="utf-8") as f:
        json.dump(key_mapping, f, indent=2)

    print(f"[+] Blinded human scoring template generated at: {output_csv_path}")
    print(f"[+] Secret unblinding key saved at: {key_mapping_path}")


if __name__ == "__main__":
    # Generate placeholder template with sample ideas
    sample_runs = [
        {"mode": "single_agent", "idea_id": f"idea-0{i}", "title": f"Startup Idea #{i}", "deliverables_path": f"exports/idea-0{i}.md"}
        for i in range(1, 4)
    ] + [
        {"mode": "multi_no_debate", "idea_id": f"idea-0{i}", "title": f"Startup Idea #{i}", "deliverables_path": f"exports/idea-0{i}.md"}
        for i in range(1, 4)
    ] + [
        {"mode": "multi_debate", "idea_id": f"idea-0{i}", "title": f"Startup Idea #{i}", "deliverables_path": f"exports/idea-0{i}.md"}
        for i in range(1, 4)
    ]
    generate_blinded_template(sample_runs)
