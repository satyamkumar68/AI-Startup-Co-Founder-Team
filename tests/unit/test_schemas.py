import pytest
from pydantic import ValidationError

from backend.app.models.schemas import (
    MarketMetric,
    CompetitorItem,
    MarketAnalystOutput,
    Persona,
    FeatureItem,
    ProductManagerOutput,
    StackChoice,
    ArchitectureComponent,
    MonthlyCostEstimate,
    TechArchitectOutput,
    PitchSlide,
    PitchWriterOutput,
    CEOCriticReview,
    PeerCritique,
    RebuttalResponse,
    RunCreateRequest,
    RunOptions,
)


def test_market_analyst_output_valid():
    output = MarketAnalystOutput(
        tam=MarketMetric(value="$50B", estimated=True, source_url="https://example.com/tam"),
        sam=MarketMetric(value="$10B", estimated=True, source_url="https://example.com/sam"),
        som=MarketMetric(value="$500M", estimated=True, source_url="https://example.com/som"),
        competitors=[
            CompetitorItem(name=f"Competitor {i}", description="Test description")
            for i in range(1, 6)
        ],
        trends=["Trend 1", "Trend 2"],
        risks=["Risk 1", "Risk 2", "Risk 3"],
        sources=["https://example.com/source1"]
    )
    assert len(output.competitors) == 5
    assert len(output.risks) == 3
    assert output.tam.estimated is True


def test_market_analyst_fails_under_5_competitors():
    with pytest.raises(ValidationError):
        MarketAnalystOutput(
            tam=MarketMetric(value="$50B"),
            sam=MarketMetric(value="$10B"),
            som=MarketMetric(value="$500M"),
            competitors=[CompetitorItem(name="C1", description="desc")],  # Only 1 competitor, needs >= 5
            risks=["R1", "R2", "R3"],
            sources=["https://example.com"]
        )


def test_market_analyst_fails_under_3_risks():
    with pytest.raises(ValidationError):
        MarketAnalystOutput(
            tam=MarketMetric(value="$50B"),
            sam=MarketMetric(value="$10B"),
            som=MarketMetric(value="$500M"),
            competitors=[CompetitorItem(name=f"C{i}", description="desc") for i in range(5)],
            risks=["R1", "R2"],  # Only 2 risks, needs >= 3
            sources=["https://example.com"]
        )


def test_product_manager_output_valid():
    output = ProductManagerOutput(
        personas=[
            Persona(name="Student", role="High Schooler", pain_points=["Hard tests"], goals=["Pass board exam"]),
            Persona(name="Tutor", role="Teacher", pain_points=["Lack of scale"], goals=["Earn income"])
        ],
        problem_statement="Students struggle with individualized exam preparation.",
        features=[
            FeatureItem(name=f"Feature {i}", priority="P0") for i in range(1, 7)
        ] + [
            FeatureItem(name="Feature 7", priority="P1"),
            FeatureItem(name="Feature 8", priority="P2"),
        ],
        mvp_scope="Buildable in 6 weeks with 2 developers.",
        user_stories=["As a student, I want instant answers...", "As a tutor, I want to track...", "As a parent, I want..."],
        success_metrics=["70% D30 retention", "NPS > 50"]
    )
    assert len(output.personas) == 2
    assert len([f for f in output.features if f.priority == "P0"]) == 6


def test_product_manager_fails_over_8_p0_features():
    with pytest.raises(ValidationError):
        ProductManagerOutput(
            personas=[
                Persona(name="P1", role="R1", pain_points=["PP1"], goals=["G1"]),
                Persona(name="P2", role="R2", pain_points=["PP2"], goals=["G2"])
            ],
            problem_statement="Test statement",
            features=[FeatureItem(name=f"P0 Feat {i}", priority="P0") for i in range(1, 10)],  # 9 P0 features!
            mvp_scope="6 weeks",
            user_stories=["Story 1", "Story 2", "Story 3"],
            success_metrics=["Metric 1", "Metric 2"]
        )


def test_tech_architect_output_valid():
    output = TechArchitectOutput(
        stack=[
            StackChoice(technology="FastAPI", category="Backend", justification="Lightweight, fast async framework"),
            StackChoice(technology="React", category="Frontend", justification="Fast rendering with rich ecosystem"),
            StackChoice(technology="PostgreSQL", category="Database", justification="Reliable ACID compliant data store")
        ],
        components=[
            ArchitectureComponent(name="API Gateway", responsibility="Routing and authentication"),
            ArchitectureComponent(name="Workflow Engine", responsibility="Agent graph execution")
        ],
        diagram_mermaid="graph TD; A[Client] --> B[API];",
        data_model="Users, Runs, Deliverables, Scores",
        scalability_notes="Horizontal worker scaling via Redis queue",
        monthly_cost_estimate=MonthlyCostEstimate(
            total_usd=45.0,
            breakdown={"Render Web Service": 25.0, "Managed Postgres": 15.0, "Redis": 5.0},
            assumptions=["< 10k monthly active users"]
        ),
        risks=["API rate limits on LLM", "Cold start delays"]
    )
    assert output.monthly_cost_estimate.total_usd == 45.0
    assert len(output.stack) == 3


def test_pitch_writer_output_valid():
    slides = [
        PitchSlide(
            slide_number=i,
            title=f"Slide {i} Title",
            bullets=["Key bullet 1", "Key bullet 2", "Key bullet 3"],
            speaker_notes="Here is what to say on this slide."
        )
        for i in range(1, 11)  # 10 slides
    ]
    output = PitchWriterOutput(slides=slides)
    assert len(output.slides) == 10


def test_pitch_writer_fails_slide_count_out_of_bounds():
    # Only 9 slides (must be 10-12)
    with pytest.raises(ValidationError):
        PitchWriterOutput(slides=[
            PitchSlide(slide_number=i, title=f"Slide {i}", bullets=["Bullet A", "Bullet B"], speaker_notes="Notes")
            for i in range(1, 10)
        ])


def test_ceo_critic_review_threshold_sync():
    # Score 8.5 -> pass_ should automatically sync to True
    review_pass = CEOCriticReview(
        target_agent="market",
        version=1,
        score=8.5,
        strengths=["Clear TAM", "Comprehensive competitor matrix"],
        weaknesses=[],
        required_changes=[],
        pass_=False  # model_validator will correct this to True
    )
    assert review_pass.pass_ is True

    # Score 6.2 -> pass_ should automatically sync to False
    review_fail = CEOCriticReview(
        target_agent="prd",
        version=1,
        score=6.2,
        strengths=["Good user stories"],
        weaknesses=["Too many P0 features"],
        required_changes=["Reduce P0 features to 5"],
        pass_=True  # model_validator will correct this to False
    )
    assert review_fail.pass_ is False


def test_run_create_request_validation():
    # Valid idea (10-500 chars)
    req = RunCreateRequest(idea="AI tutor for Class 10 students in India")
    assert req.idea == "AI tutor for Class 10 students in India"
    assert req.options.score_threshold == 7.0
    assert req.options.debate_rounds == 2

    # Too short (< 10 chars)
    with pytest.raises(ValidationError):
        RunCreateRequest(idea="Short")
