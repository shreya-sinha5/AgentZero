"""AgentZero Autonomous Investigation and Repair Orchestration Workflow."""
import time
from typing import Dict, Any, List, Optional
from ..models import (
    Incident, IncidentStatus, FailureType,
    DiagnosticReport, Finding, RootCauseReport, RootCauseHypothesis,
    RepairPatch, TestResults, SecurityResults
)
from ..tools.gateway import gateway, ToolGateway
from ..services.incident_service import incident_service

def init_default_tools(gw: ToolGateway):
    """Register tool implementations into the Tool Gateway."""
    # Diagnostic tools
    gw.register_tool("query_metrics", lambda query, service="monitored-ecommerce": {
        "service": service,
        "query": query,
        "samples": [
            {"metric": query, "value": 2.45, "timestamp": time.time() - 30},
            {"metric": query, "value": 3.10, "timestamp": time.time() - 15},
            {"metric": query, "value": 3.80, "timestamp": time.time()}
        ],
        "status": "anomalous"
    })
    
    gw.register_tool("search_logs", lambda service="monitored-ecommerce", error_pattern="error": {
        "service": service,
        "matches": [
            f"ERROR: Slow query detected in {service} on endpoint /api/products",
            f"WARNING: Database connection pool utilization at 92%"
        ]
    })
    
    gw.register_tool("analyze_traces", lambda service="monitored-ecommerce": {
        "service": service,
        "span_count": 14,
        "critical_path": ["GET /api/products", "SQL SELECT * FROM products", "sqlite3.cursor.fetchall"],
        "bottleneck_span": "SQL SELECT * FROM products (duration: 1.82s)"
    })

    # Root Cause tools
    gw.register_tool("get_dependency_graph", lambda service="monitored-ecommerce": {
        "service": service,
        "upstream": ["api-gateway", "client-web"],
        "downstream": ["sqlite-database", "payment-service"],
        "healthy": ["payment-service"],
        "degraded": ["sqlite-database"]
    })

    gw.register_tool("search_knowledge_base", lambda query="": {
        "similar_incidents": [
            {"incident_id": "INC-0994", "root_cause": "Unindexed table scan", "similarity": 0.88}
        ]
    })

    # Repair tools
    gw.register_tool("read_source_file", lambda path="": {
        "path": path,
        "content": "# Simulated source file read via Tool Gateway"
    })

    gw.register_tool("create_temp_branch", lambda incident_id: {
        "branch": f"agentzero/inc-{incident_id.lower()}-1",
        "created_at": time.time()
    })

    gw.register_tool("generate_git_patch", lambda branch, diff, rationale: {
        "branch": branch,
        "patch_hash": "a8f3b21c",
        "lines_added": 3,
        "lines_removed": 1
    })

    # Testing tools
    gw.register_tool("run_sandbox_tests", lambda branch: {
        "branch": branch,
        "tests_passed": 13,
        "tests_failed": 0,
        "duration_seconds": 1.25,
        "perf_delta": "-85% latency improvement"
    })

    # Security tools
    gw.register_tool("run_bandit_scan", lambda diff="": {
        "scanned_lines": len(diff.splitlines()),
        "issues_found": [line for line in ["eval(", "exec(", "DROP TABLE"] if line in diff],
        "verdict": "fail" if any(line in diff for line in ["eval(", "exec(", "DROP TABLE"]) else "pass"
    })

    gw.register_tool("run_semgrep_scan", lambda diff="": {
        "rules_checked": 24,
        "findings": []
    })

    gw.register_tool("run_dependency_scan", lambda: {
        "vulnerable_packages": []
    })

# Register default tools into gateway
init_default_tools(gateway)

class Orchestrator:
    def __init__(self, gw: ToolGateway = gateway):
        self.gw = gw

    def run_investigation(self, incident_id: str) -> Incident:
        """Execute the multi-agent investigation and repair workflow."""
        inc = incident_service.get_incident(incident_id)
        if not inc:
            raise KeyError(f"Incident '{incident_id}' not found")

        # 1. State: DETECTED -> INVESTIGATING
        if inc.status == IncidentStatus.DETECTED:
            incident_service.transition_incident(incident_id, IncidentStatus.INVESTIGATING)

        # 2. Diagnostic Agent Execution
        metric_data = self.gw.execute("diagnostic_agent", "query_metrics", {"query": inc.alerts[0].metric if inc.alerts else "latency"})
        log_data = self.gw.execute("diagnostic_agent", "search_logs", {"service": inc.service})
        trace_data = self.gw.execute("diagnostic_agent", "analyze_traces", {"service": inc.service})

        findings = [
            Finding(observation=f"Anomalous metric confirmed: {inc.title}", evidence=f"Metrics: {metric_data['samples'][-1]}"),
            Finding(observation=f"Identified bottleneck span: {trace_data['bottleneck_span']}", evidence="Trace latency breakdown"),
            Finding(observation="Log correlation shows database pool saturation warnings", evidence=str(log_data["matches"]))
        ]

        inc.diagnostic_report = DiagnosticReport(
            incident_id=incident_id,
            findings=findings,
            recommendations=["Inspect query execution plan", "Check index coverage", "Verify pool size"],
            confidence=0.92,
            failure_type=inc.failure_type
        )

        # 3. State: INVESTIGATING -> ROOT_CAUSE_IDENTIFIED
        incident_service.transition_incident(incident_id, IncidentStatus.ROOT_CAUSE_IDENTIFIED)

        dep_data = self.gw.execute("root_cause_agent", "get_dependency_graph", {"service": inc.service})
        kb_data = self.gw.execute("root_cause_agent", "search_knowledge_base", {"query": inc.service})

        hypotheses = [
            RootCauseHypothesis(
                cause=f"Full table scan on {inc.service} without database index",
                evidence=[findings[1].observation, f"Degraded component: {dep_data['degraded']}"],
                confidence=0.89,
                would_be_disproved_by="EXPLAIN shows Index Scan instead of Sequential Scan"
            ),
            RootCauseHypothesis(
                cause="Transient network partition between service and database",
                evidence=["Connection pool wait times"],
                confidence=0.11,
                would_be_disproved_by="Ping and TCP handshake latencies remain below 1ms"
            )
        ]

        inc.root_cause_report = RootCauseReport(
            incident_id=incident_id,
            hypotheses=hypotheses,
            selected=hypotheses[0].cause,
            causal_chain=[
                "Deploy introduces unindexed query filter",
                "Full table scan executes on product lookup",
                "Connection pool exhausts under load",
                "API requests timeout at 2000ms+ threshold"
            ],
            confidence=0.89
        )

        # 4. State: ROOT_CAUSE_IDENTIFIED -> REPAIR_PROPOSED
        incident_service.transition_incident(incident_id, IncidentStatus.REPAIR_PROPOSED)

        branch_info = self.gw.execute("repair_agent", "create_temp_branch", {"incident_id": incident_id})
        generated_diff = (
            "--- a/database/schema.sql\n"
            "+++ b/database/schema.sql\n"
            "@@ -10,3 +10,4 @@\n"
            "+CREATE INDEX idx_products_category ON products(category);\n"
        )
        self.gw.execute("repair_agent", "generate_git_patch", {
            "branch": branch_info["branch"],
            "diff": generated_diff,
            "rationale": "Add database index on products(category) to eliminate full table scan."
        })

        inc.repair_patch = RepairPatch(
            incident_id=incident_id,
            branch=branch_info["branch"],
            diff=generated_diff,
            rationale="Add database index on products(category) to eliminate sequential table scan.",
            potential_side_effects=["Slight increase in write latency during insert (<2%)"]
        )

        # 5. State: REPAIR_PROPOSED -> VALIDATING
        incident_service.transition_incident(incident_id, IncidentStatus.VALIDATING)

        test_data = self.gw.execute("testing_agent", "run_sandbox_tests", {"branch": branch_info["branch"]})
        inc.test_results = TestResults(
            incident_id=incident_id,
            verdict="pass",
            unit_tests={"passed": test_data["tests_passed"], "failed": test_data["tests_failed"]},
            integration_tests={"smoke_tests": "passed"},
            perf_delta=test_data["perf_delta"]
        )

        security_data = self.gw.execute("security_agent", "run_bandit_scan", {"diff": generated_diff})
        inc.security_results = SecurityResults(
            incident_id=incident_id,
            verdict=security_data["verdict"],
            vulnerabilities=security_data["issues_found"],
            veto_deployment=(security_data["verdict"] == "fail")
        )

        # 6. State: VALIDATING -> AWAITING_APPROVAL (if passed)
        if inc.test_results.verdict == "pass" and not inc.security_results.veto_deployment:
            incident_service.transition_incident(incident_id, IncidentStatus.AWAITING_APPROVAL)
        else:
            incident_service.transition_incident(incident_id, IncidentStatus.ESCALATED)

        return inc

orchestrator = Orchestrator()
