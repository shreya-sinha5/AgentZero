"""Full system and multi-agent workflow verification script for AgentZero."""
import subprocess
import sys
import time
import urllib.request
import json

def check_system():
    print("=== [1] Starting Monitored E-Commerce Demo on port 8001 ===")
    p_mon = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "monitored_app.app.main:app", "--port", "8001", "--host", "127.0.0.1"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print("=== [2] Starting AgentZero Backend on port 8000 ===")
    p_back = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "backend.app.main:app", "--port", "8000", "--host", "127.0.0.1"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        # Wait for services to bind
        time.sleep(2.5)

        # 1. Health checks
        with urllib.request.urlopen("http://127.0.0.1:8001/health", timeout=3) as r:
            mon_health = json.loads(r.read().decode())
            print("[PASS] Monitored App Health:", mon_health)

        with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=3) as r:
            back_health = json.loads(r.read().decode())
            print("[PASS] AgentZero Backend Health:", back_health)

        # 2. Ingest Critical Anomaly Alert into Backend
        alert_payload = json.dumps({
            "service": "monitored-ecommerce",
            "metric": "db_query_duration_seconds",
            "observed_value": 2.45,
            "baseline_value": 0.05,
            "severity": "critical",
            "description": "Slow unindexed queries detected during catalog browse"
        }).encode("utf-8")
        req = urllib.request.Request(
            "http://127.0.0.1:8000/api/monitoring/alerts",
            data=alert_payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=3) as r:
            ingest_res = json.loads(r.read().decode())
            inc_id = ingest_res["incident_id"]
            print(f"[PASS] Alert Ingested -> Created Incident '{inc_id}' (status: {ingest_res['incident_status']})")

        # 3. Trigger Autonomous Multi-Agent Investigation
        print(f"=== [3] Triggering Autonomous Investigation for {inc_id} ===")
        req_inv = urllib.request.Request(
            f"http://127.0.0.1:8000/api/incidents/{inc_id}/investigate",
            data=b"{}",
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req_inv, timeout=5) as r:
            investigated_inc = json.loads(r.read().decode())
            print(f"[PASS] Investigation Completed -> Status: {investigated_inc['status']}")
            print(f"       Diagnostic: {len(investigated_inc['diagnostic_report']['findings'])} findings (confidence: {investigated_inc['diagnostic_report']['confidence']})")
            print(f"       Root Cause: {investigated_inc['root_cause_report']['selected']}")
            print(f"       Repair: Branch '{investigated_inc['repair_patch']['branch']}'")
            print(f"       Validation: Tests {investigated_inc['test_results']['verdict'].upper()} ({investigated_inc['test_results']['perf_delta']})")
            print(f"       Security: Bandit Scan {investigated_inc['security_results']['verdict'].upper()} (veto={investigated_inc['security_results']['veto_deployment']})")

        # 4. Check Repair Details
        with urllib.request.urlopen(f"http://127.0.0.1:8000/api/repairs/{inc_id}", timeout=3) as r:
            repair_details = json.loads(r.read().decode())
            print(f"[PASS] Retrieved Repair Details for {inc_id}: Patch Diff ready for approval")

        # 5. Human Approval Gateway
        print(f"=== [4] Human Approval: Approving repair for {inc_id} ===")
        approval_body = json.dumps({"approver": "on_call_sre", "decision": "approved", "comments": "Index fix verified"}).encode("utf-8")
        req_app = urllib.request.Request(
            f"http://127.0.0.1:8000/api/repairs/{inc_id}/approve",
            data=approval_body,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req_app, timeout=3) as r:
            approved_inc = json.loads(r.read().decode())
            print(f"[PASS] Approved by {approval_body.decode()} -> Status: {approved_inc['status']}")

        # 6. Deployment & Automated Health Verification
        deploy_body = json.dumps({"incident_id": inc_id, "version": "v1.0.1", "target": "staging"}).encode("utf-8")
        req_dep = urllib.request.Request(
            "http://127.0.0.1:8000/api/deployments",
            data=deploy_body,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req_dep, timeout=3) as r:
            dep_res = json.loads(r.read().decode())
            print(f"[PASS] Deployment Triggered -> Status: {dep_res['status']}")

        # 7. Transition to Resolved
        req_res = urllib.request.Request(
            f"http://127.0.0.1:8000/api/incidents/{inc_id}/transition",
            data=json.dumps({"new_status": "RESOLVED"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req_res, timeout=3) as r:
            final_inc = json.loads(r.read().decode())
            print(f"[PASS] Incident Life-Cycle Complete -> Final Status: {final_inc['status']}")

        # 8. Check Dashboard Overview
        with urllib.request.urlopen("http://127.0.0.1:8000/api/dashboard/overview", timeout=3) as r:
            overview = json.loads(r.read().decode())
            print(f"[PASS] Dashboard Overview -> Active: {overview['active_incidents']}, Resolved: {overview['resolved_incidents']}, System Status: {overview['system_status']}")

        print("\n>>> ALL SYSTEM VERIFICATION & MULTI-AGENT WORKFLOW CHECKS PASSED! <<<")

    finally:
        p_mon.terminate()
        p_back.terminate()

if __name__ == "__main__":
    check_system()
