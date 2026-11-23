"""Tests for Incident lifecycle state machine and deduplication."""
import pytest
from backend.app.models import AlertPayload, IncidentStatus, IncidentSeverity, FailureType
from backend.app.services.incident_service import IncidentService, InvalidStateTransitionError

def test_incident_creation_and_type_inference():
    svc = IncidentService()
    alert = AlertPayload(
        service="payment-api",
        metric="db_query_latency",
        observed_value=3.5,
        baseline_value=0.05,
        severity=IncidentSeverity.CRITICAL
    )
    incident = svc.process_alert(alert)
    assert incident.incident_id.startswith("INC-")
    assert incident.status == IncidentStatus.DETECTED
    assert incident.failure_type == FailureType.DATABASE
    assert len(incident.alerts) == 1

def test_alert_deduplication():
    svc = IncidentService()
    alert1 = AlertPayload(service="order-service", metric="response_time", observed_value=2000, baseline_value=100)
    alert2 = AlertPayload(service="order-service", metric="response_time", observed_value=2500, baseline_value=100)

    inc1 = svc.process_alert(alert1)
    inc2 = svc.process_alert(alert2)

    # Both alerts should be grouped into the same incident
    assert inc1.incident_id == inc2.incident_id
    assert len(inc2.alerts) == 2

def test_valid_state_transitions():
    svc = IncidentService()
    alert = AlertPayload(service="api-gateway", metric="error_rate", observed_value=0.1, baseline_value=0.001)
    incident = svc.process_alert(alert)
    inc_id = incident.incident_id

    # DETECTED -> INVESTIGATING
    inc = svc.transition_incident(inc_id, IncidentStatus.INVESTIGATING)
    assert inc.status == IncidentStatus.INVESTIGATING

    # INVESTIGATING -> ROOT_CAUSE_IDENTIFIED
    inc = svc.transition_incident(inc_id, IncidentStatus.ROOT_CAUSE_IDENTIFIED)
    assert inc.status == IncidentStatus.ROOT_CAUSE_IDENTIFIED

    # ROOT_CAUSE_IDENTIFIED -> REPAIR_PROPOSED
    inc = svc.transition_incident(inc_id, IncidentStatus.REPAIR_PROPOSED)
    assert inc.status == IncidentStatus.REPAIR_PROPOSED

    # REPAIR_PROPOSED -> VALIDATING
    inc = svc.transition_incident(inc_id, IncidentStatus.VALIDATING)
    assert inc.status == IncidentStatus.VALIDATING

    # VALIDATING -> AWAITING_APPROVAL
    inc = svc.transition_incident(inc_id, IncidentStatus.AWAITING_APPROVAL)
    assert inc.status == IncidentStatus.AWAITING_APPROVAL

    # Approval -> DEPLOYING
    inc = svc.record_approval(inc_id, approver="senior_sre", decision="approved")
    assert inc.status == IncidentStatus.DEPLOYING

    # Deployment verified -> RESOLVED
    inc = svc.record_deployment(inc_id, version="v1.0.1", status="verified")
    assert inc.status == IncidentStatus.RESOLVED

def test_invalid_state_transition_rejected():
    svc = IncidentService()
    alert = AlertPayload(service="api", metric="latency", observed_value=500, baseline_value=50)
    incident = svc.process_alert(alert)
    
    # Cannot jump directly from DETECTED to DEPLOYING without investigation/approval
    with pytest.raises(InvalidStateTransitionError):
        svc.transition_incident(incident.incident_id, IncidentStatus.DEPLOYING)
