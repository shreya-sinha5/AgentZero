"""Tests for Backend REST API endpoints."""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_api_health_check():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

def test_alert_ingestion_and_query():
    # 1. Ingest alert
    alert_data = {
        "service": "monitored-ecommerce",
        "metric": "response_latency",
        "observed_value": 3200.0,
        "baseline_value": 200.0,
        "severity": "critical",
        "description": "High latency on checkout endpoint"
    }
    resp = client.post("/api/monitoring/alerts", json=alert_data)
    assert resp.status_code == 200
    res_json = resp.json()
    assert res_json["status"] == "received"
    inc_id = res_json["incident_id"]

    # 2. Get incident by ID
    resp = client.get(f"/api/incidents/{inc_id}")
    assert resp.status_code == 200
    inc_data = resp.json()
    assert inc_data["incident_id"] == inc_id
    assert inc_data["service"] == "monitored-ecommerce"

    # 3. Overview stats
    resp = client.get("/api/dashboard/overview")
    assert resp.status_code == 200
    overview = resp.json()
    assert overview["total_incidents"] >= 1
    assert overview["active_incidents"] >= 1
