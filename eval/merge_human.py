import os
import csv
import json
import statistics
from typing import Dict, Any, List


def merge_human_scores(
    csv_path: str = "eval/human_scoring/blinded_scoring_sheet.csv",
    key_mapping_path: str = "eval/human_scoring/.key_mapping.json",
    output_summary_path: str = "eval/results/human_evaluation_summary.json"
) -> Dict[str, Any]:
    """Ingest blinded human scoring CSV, unblind using key mapping, and compute statistics.
    
    Adheres strictly to the rule:
    - Never fabricate human scores.
    - If unfilled, explicitly report 'not measured'.
    """
    if not os.path.exists(csv_path) or not os.path.exists(key_mapping_path):
        return {
            "status": "not_measured",
            "message": "Blinded scoring sheet or key mapping not found. Human evaluation has not been conducted."
        }

    with open(key_mapping_path, "r", encoding="utf-8") as f:
        key_mapping = json.load(f)

    mode_scores: Dict[str, List[float]] = {
        "single_agent": [],
        "multi_no_debate": [],
        "multi_debate": []
    }

    numeric_columns = [
        "market_realism_1_to_5",
        "internal_consistency_1_to_5",
        "feasibility_cost_1_to_5",
        "specificity_1_to_5",
        "risk_awareness_1_to_5"
    ]

    scored_entries = 0

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            blind_id = row.get("blind_id")
            if not blind_id or blind_id not in key_mapping:
                continue

            mode = key_mapping[blind_id].get("mode")
            if mode not in mode_scores:
                continue

            vals = []
            for col in numeric_columns:
                raw_val = row.get(col, "").strip()
                if raw_val:
                    try:
                        vals.append(float(raw_val))
                    except ValueError:
                        pass

            if vals:
                # Average for this item
                item_avg = sum(vals) / len(vals)
                mode_scores[mode].append(item_avg)
                scored_entries += 1

    if scored_entries == 0:
        summary = {
            "status": "not_measured",
            "total_scored_ideas": 0,
            "message": "Blinded CSV contains no human scores yet. Owner/peers must complete scoring."
        }
    else:
        summary = {
            "status": "completed",
            "total_scored_ideas": scored_entries,
            "modes": {}
        }
        for mode, s_list in mode_scores.items():
            if s_list:
                mean_val = round(statistics.mean(s_list), 2)
                stdev_val = round(statistics.stdev(s_list), 2) if len(s_list) > 1 else 0.0
                summary["modes"][mode] = {
                    "count": len(s_list),
                    "mean_5": mean_val,
                    "composite_10": round(mean_val * 2.0, 2),
                    "stdev": stdev_val
                }
            else:
                summary["modes"][mode] = {"count": 0, "mean_5": "not measured", "composite_10": "not measured"}

    os.makedirs(os.path.dirname(output_summary_path), exist_ok=True)
    with open(output_summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"[+] Merged human scores written to: {output_summary_path}")
    return summary


if __name__ == "__main__":
    merge_human_scores()
