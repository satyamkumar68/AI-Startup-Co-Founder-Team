import pytest
from pathlib import Path
from eval.run_ablation import load_dataset, run_ablation_study, generate_markdown_report


def test_load_dataset():
    dataset_path = Path("eval/ideas.jsonl")
    ideas = load_dataset(dataset_path, limit=3)
    assert len(ideas) == 3
    assert "idea" in ideas[0]
    assert "quality_tier" in ideas[0]


@pytest.mark.asyncio
async def test_run_ablation_study_offline(tmp_path):
    dataset_path = Path("eval/ideas.jsonl")
    ideas = load_dataset(dataset_path, limit=2)
    
    results = await run_ablation_study(
        ideas=ideas,
        output_dir=tmp_path,
        mock_offline=True
    )

    assert "metadata" in results
    assert "aggregates" in results
    assert "single_agent" in results["aggregates"]
    assert "multi_debate" in results["aggregates"]
    assert results["aggregates"]["multi_debate"]["avg_composite_score"] > results["aggregates"]["single_agent"]["avg_composite_score"]

    # Check generated files
    assert (tmp_path / "ablation_results.json").exists()
    assert (tmp_path / "ABLATION.md").exists()
    
    md_content = (tmp_path / "ABLATION.md").read_text(encoding="utf-8")
    assert "# Empirical Ablation Study" in md_content
    assert "Composite Score" in md_content
