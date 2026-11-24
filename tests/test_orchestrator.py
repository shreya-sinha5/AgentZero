"""Tests for Orchestrator investigation and repair workflow."""
import pytest
from backend.app.models import AlertPayload, IncidentSeverity, IncidentStatus
from backend.app.services.incident_service import IncidentService
from backend.app.tools.gateway import ToolGateway
from backend.app.orchestration.workflow import Orchestrator, init_default_tools
from backend.app.api.routes import investigate_incident, get_repair_details

def test_full_autonomous_investigation_and_repair():
    gw = ToolGateway()
    init_default_tools(gw)
    svc = IncidentService()
    orch = Orchestrator(gw=gw)

    # 1. Alert arrives -> incident in DETECTED status
    alert = AlertPayload(
        service="monitored-ecommerce",
        metric="db_query_duration_seconds",
        observed_value=2.45,
        baseline_value=0.05,
        severity=IncidentSeverity.CRITICAL
    )
    inc = svc.process_alert(alert)
    assert inc.status == IncidentStatus.DETECTED

    # Patch incident_service reference for test
    from backend.app.orchestration import workflow
    workflow.incident_service = svc

    # 2. Run investigation
    resolved_inc = orch.run_investigation(inc.incident_id)

    # Verify all agent outputs are attached
    assert resolved_inc.diagnostic_report is not None
    assert len(resolved_inc.diagnostic_report.findings) >= 2
    assert resolved_inc.diagnostic_report.confidence > 0.8

    assert resolved_inc.root_cause_report is not None
    assert len(resolved_inc.root_cause_report.hypotheses) >= 1
    assert "Full table scan" in resolved_inc.root_cause_report.selected
    assert len(resolved_inc.root_cause_report.causal_chain) >= 2

    assert resolved_inc.repair_patch is not None
    assert "agentzero/inc-" in resolved_inc.repair_patch.branch
    assert "CREATE INDEX" in resolved_inc.repair_patch.diff

    assert resolved_inc.test_results is not None
    assert resolved_inc.test_results.verdict == "pass"

    assert resolved_inc.security_results is not None
    assert resolved_inc.security_results.verdict == "pass"
    assert resolved_inc.security_results.veto_deployment is False

    # 3. State must be AWAITING_APPROVAL
    assert resolved_inc.status == IncidentStatus.AWAITING_APPROVAL

def test_security_veto_blocks_deployment_approval():
    gw = ToolGateway()
    init_default_tools(gw)
    svc = IncidentService()
    orch = Orchestrator(gw=gw)

    # Mock bandit to inject a security veto
    gw.register_tool("run_bandit_scan", lambda diff="": {
        "verdict": "fail",
        "issues_found": ["Critical: eval() invocation detected in patch"]
    })

    alert = AlertPayload(service="monitored-ecommerce", metric="latency", observed_value=3000, baseline_value=100)
    inc = svc.process_alert(alert)

    from backend.app.orchestration import workflow
    workflow.incident_service = svc

    vetoed_inc = orch.run_investigation(inc.incident_id)

    assert vetoed_inc.security_results.verdict == "fail"
    assert vetoed_inc.security_results.veto_deployment is True
    # If vetoed, incident must NOT be in AWAITING_APPROVAL; it must be ESCALATED
    assert vetoed_inc.status == IncidentStatus.ESCALATED
