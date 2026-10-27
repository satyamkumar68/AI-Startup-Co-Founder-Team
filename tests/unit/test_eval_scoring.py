import os
import csv
import json
import pytest
from eval.score import RubricBreakdown, EvaluationJudge
from eval.generate_human_csv import generate_blinded_template
from eval.merge_human import merge_human_scores


def test_rubric_breakdown_composite_calculation():
    rubric = RubricBreakdown(
        market_realism=4.0,
        internal_consistency=4.5,
        feasibility_cost=3.5,
        specificity=4.0,
        risk_awareness=4.0,
        rationale={"test": "ok"}
    )
    # Average is (4.0+4.5+3.5+4.0+4.0)/5 = 20.0/5 = 4.0
    # composite_10 = 4.0 * 2.0 = 8.0
    assert rubric.composite_10 == 8.0


def test_evaluation_judge_heuristic_score():
    judge = EvaluationJudge()
    deliverables = {
        "market": {
            "tam": {"value": "$5B", "source_url": "https://gartner.com/report"},
            "competitors": [{"name": f"C{i}"} for i in range(5)],
            "risks": ["R1", "R2", "R3"]
        },
        "prd": {
            "features": [{"name": "F1"}],
            "personas": [{"name": "P1"}, {"name": "P2"}],
            "user_stories": ["S1", "S2", "S3"],
            "success_metrics": ["M1", "M2"]
        },
        "architecture": {
            "components": [{"name": "API"}],
            "monthly_cost_estimate": {"total_usd": 75.0, "breakdown": {"compute": 50.0}},
            "risks": ["TechRisk1", "TechRisk2"]
        },
        "pitch": {
            "slides": [{"title": f"Slide {i}"} for i in range(10)]
        }
    }

    scored = judge.heuristic_score(deliverables)
    assert 1.0 <= scored.market_realism <= 5.0
    assert 1.0 <= scored.internal_consistency <= 5.0
    assert 1.0 <= scored.feasibility_cost <= 5.0
    assert 1.0 <= scored.specificity <= 5.0
    assert 1.0 <= scored.risk_awareness <= 5.0
    assert scored.composite_10 >= 7.0


@pytest.mark.asyncio
async def test_evaluation_judge_compare_pairwise():
    from unittest.mock import AsyncMock, patch
    judge = EvaluationJudge()
    
    score_high = RubricBreakdown(
        market_realism=4.5,
        internal_consistency=4.5,
        feasibility_cost=4.0,
        specificity=4.5,
        risk_awareness=4.5
    )
    score_low = RubricBreakdown(
        market_realism=2.0,
        internal_consistency=2.0,
        feasibility_cost=2.0,
        specificity=2.0,
        risk_awareness=2.0
    )

    with patch.object(judge, "score_deliverables", side_effect=[score_high, score_low]):
        res = await judge.compare_pairwise("AI edtech", {}, {}, "High Quality", "Low Quality")
        assert res.winner == "A"
        assert res.margin == "decisive"


def test_blinded_human_scoring_workflow(tmp_path):
    csv_path = str(tmp_path / "blinded.csv")
    key_path = str(tmp_path / "keys.json")
    summary_path = str(tmp_path / "summary.json")

    sample_runs = [
        {"mode": "single_agent", "idea_id": "idea-01", "title": "Idea 1", "deliverables_path": "x.md"},
        {"mode": "multi_debate", "idea_id": "idea-01", "title": "Idea 1", "deliverables_path": "y.md"}
    ]

    # 1. Generate template
    generate_blinded_template(sample_runs, output_csv_path=csv_path, key_mapping_path=key_path)
    assert os.path.exists(csv_path)
    assert os.path.exists(key_path)

    # 2. Before scores are filled
    res_empty = merge_human_scores(csv_path, key_path, summary_path)
    assert res_empty["status"] == "not_measured"

    # 3. Fill in human score for one item
    with open(csv_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    rows[0]["market_realism_1_to_5"] = "4.5"
    rows[0]["internal_consistency_1_to_5"] = "4.0"
    rows[0]["feasibility_cost_1_to_5"] = "4.0"
    rows[0]["specificity_1_to_5"] = "4.5"
    rows[0]["risk_awareness_1_to_5"] = "4.0"

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    res_filled = merge_human_scores(csv_path, key_path, summary_path)
    assert res_filled["status"] == "completed"
    assert res_filled["total_scored_ideas"] == 1
