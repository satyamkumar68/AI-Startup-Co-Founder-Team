import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.api.websocket import ws_manager


@pytest.fixture
def client():
    # Disable background workflow execution and DB connection attempts during unit API tests
    with patch("backend.app.api.routes.dispatch_run"), patch("backend.app.main.init_db"):
        with TestClient(app) as test_client:
            yield test_client


def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_create_run_success(client):
    payload = {
        "idea": "An AI-powered tutor for CBSE Class 10 students in India.",
        "options": {
            "debate_rounds": 2,
            "score_threshold": 7.0
        }
    }
    response = client.post("/api/v1/runs", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert "run_id" in data
    assert data["status"] == "queued"


def test_create_run_validation_error(client):
    # Idea too short (< 10 chars)
    payload = {"idea": "Tiny"}
    response = client.post("/api/v1/runs", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_list_runs(client):
    # Create a run first
    client.post("/api/v1/runs", json={"idea": "Continuous compliance platform for startups."})
    
    response = client.get("/api/v1/runs?limit=10&offset=0")
    assert response.status_code == 200
    runs = response.json()
    assert isinstance(runs, list)


def test_get_run_detail(client):
    create_resp = client.post(
        "/api/v1/runs",
        json={"idea": "Automated Cloud FinOps platform for YC startups."}
    )
    run_id = create_resp.json()["run_id"]

    detail_resp = client.get(f"/api/v1/runs/{run_id}")
    assert detail_resp.status_code == 200
    data = detail_resp.json()
    assert data["run_id"] == run_id
    assert "Automated Cloud FinOps" in data["idea"]


def test_cancel_run(client):
    create_resp = client.post(
        "/api/v1/runs",
        json={"idea": "AI Legal Contract Risk Analyzer for Freelancers."}
    )
    run_id = create_resp.json()["run_id"]

    cancel_resp = client.post(f"/api/v1/runs/{run_id}/cancel")
    assert cancel_resp.status_code == 200
    data = cancel_resp.json()
    assert data["status"] == "cancelled"


def test_rerun_endpoint(client):
    create_resp = client.post(
        "/api/v1/runs",
        json={"idea": "AI Voice Receptionist for Dental Clinics."}
    )
    original_run_id = create_resp.json()["run_id"]

    rerun_resp = client.post(
        f"/api/v1/runs/{original_run_id}/rerun",
        json={"idea": "AI Voice Receptionist for Veterinary Clinics."}
    )
    assert rerun_resp.status_code == 202
    data = rerun_resp.json()
    assert "run_id" in data
    assert data["run_id"] != original_run_id


def test_get_debate_transcript(client):
    create_resp = client.post(
        "/api/v1/runs",
        json={"idea": "Personalized Recipe and Grocery Cart Generator."}
    )
    run_id = create_resp.json()["run_id"]

    debate_resp = client.get(f"/api/v1/runs/{run_id}/debate")
    assert debate_resp.status_code == 200
    data = debate_resp.json()
    assert data["run_id"] == run_id
    assert "messages" in data


def test_websocket_connection(client):
    run_id = "test-ws-run-123"
    with client.websocket_connect(f"/ws/runs/{run_id}") as websocket:
        # Send a ping message from client
        websocket.send_text("ping")


def test_export_clean_production_filename(client):
    """Verify that export endpoint returns clean TitleCase filename and proper headers."""
    create_resp = client.post(
        "/api/v1/runs",
        json={"idea": "AI tool that scans Shopify product catalogs and automatically rewrites descriptions."}
    )
    run_id = create_resp.json()["run_id"]

    # Test PDF export
    resp_pdf = client.get(f"/api/v1/runs/{run_id}/export?format=pdf")
    assert resp_pdf.status_code == 200
    assert resp_pdf.headers["content-type"] == "application/pdf"
    disposition = resp_pdf.headers.get("content-disposition", "")
    assert "attachment" in disposition
    assert ".pdf" in disposition
    assert "Shopify" in disposition

    # Test PPTX export
    resp_pptx = client.get(f"/api/v1/runs/{run_id}/export?format=pptx")
    assert resp_pptx.status_code == 200
    assert "presentation" in resp_pptx.headers["content-type"]
    assert ".pptx" in resp_pptx.headers.get("content-disposition", "")

    # Test Markdown export
    resp_md = client.get(f"/api/v1/runs/{run_id}/export?format=md")
    assert resp_md.status_code == 200
    assert "text/markdown" in resp_md.headers["content-type"]
    assert ".md" in resp_md.headers.get("content-disposition", "")

    # Test CSV export
    resp_csv = client.get(f"/api/v1/runs/{run_id}/export?format=csv")
    assert resp_csv.status_code == 200
    assert "text/csv" in resp_csv.headers["content-type"]
    assert ".csv" in resp_csv.headers.get("content-disposition", "")


def test_direct_download_with_filename_in_url(client):
    """Verify that GET /runs/{run_id}/download/{filename} serves correct file and preserves extension."""
    create_resp = client.post(
        "/api/v1/runs",
        json={"idea": "AI Tutor for CBSE Class 10 Students"}
    )
    run_id = create_resp.json()["run_id"]

    # Direct download for pitch deck
    direct_resp = client.get(f"/api/v1/runs/{run_id}/download/AI_Tutor_CBSE_Pitch_Deck.pptx")
    assert direct_resp.status_code == 200
    assert "presentation" in direct_resp.headers["content-type"]
    assert "AI_Tutor_CBSE_Pitch_Deck.pptx" in direct_resp.headers.get("content-disposition", "")
    assert len(direct_resp.content) > 0

    # Direct download for executive report PDF
    direct_pdf = client.get(f"/api/v1/runs/{run_id}/download/AI_Tutor_Executive_Report.pdf")
    assert direct_pdf.status_code == 200
    assert direct_pdf.headers["content-type"] == "application/pdf"
    assert "AI_Tutor_Executive_Report.pdf" in direct_pdf.headers.get("content-disposition", "")
    assert direct_pdf.content.startswith(b"%PDF")


def test_get_run_data_json_header(client):
    """Verify GET /runs/{run_id} includes Content-Disposition for browser and Swagger UI downloads."""
    create_resp = client.post(
        "/api/v1/runs",
        json={"idea": "Smart Inventory Management Platform"}
    )
    run_id = create_resp.json()["run_id"]

    get_resp = client.get(f"/api/v1/runs/{run_id}")
    assert get_resp.status_code == 200
    disposition = get_resp.headers.get("content-disposition", "")
    assert "inline" in disposition
    assert ".json" in disposition
    assert "Smart_Inventory" in disposition

