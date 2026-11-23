"""Tests for Backend REST API handlers and validation."""
import pytest
from backend.app.main import health
from backend.app.api.routes import (
    get_dashboard_overview,
    ingest_alert,
    get_incident,
    list_incidents,
    approve_repair,
    ApprovalRequestBody,
)
from backend.app.models import AlertPayload, IncidentSeverity, IncidentStatus

def test_api_health_check():
    res = health()
    assert res == {"status": "ok", "service": "agentzero-backend"}

def test_alert_ingestion_and_query():
    # 1. Ingest alert
    alert = AlertPayload(
        service="monitored-ecommerce",
        metric="response_latency",
        observed_value=3200.0,
        baseline_value=200.0,
        severity=IncidentSeverity.CRITICAL,
        description="High latency on checkout endpoint"
    )
    res = ingest_alert(alert)
    assert res["status"] == "received"
    inc_id = res["incident_id"]
    assert res["alerts_count"] >= 1

    # 2. Query incident
    inc = get_incident(inc_id)
    assert inc.incident_id == inc_id
    assert inc.service == "monitored-ecommerce"
    assert inc.status == IncidentStatus.DETECTED

    # 3. List incidents
    incidents = list_incidents()
    assert len(incidents) >= 1

    # 4. Overview stats
    overview = get_dashboard_overview()
    assert overview["total_incidents"] >= 1
    assert overview["active_incidents"] >= 1
