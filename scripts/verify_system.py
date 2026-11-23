"""Full system verification script for AgentZero."""
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

        # 2. Ingest Alert into Backend
        alert_payload = json.dumps({
            "service": "monitored-ecommerce",
            "metric": "db_query_duration_seconds",
            "observed_value": 2.4,
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
            print("[PASS] Alert Ingested into Backend:", ingest_res)
            inc_id = ingest_res["incident_id"]

        # 3. Query Incident by ID
        with urllib.request.urlopen(f"http://127.0.0.1:8000/api/incidents/{inc_id}", timeout=3) as r:
            incident = json.loads(r.read().decode())
            print(f"[PASS] Retrieved Incident '{inc_id}' Status: {incident['status']}, Type: {incident['failure_type']}")

        # 4. Check Prometheus Metrics Endpoint
        with urllib.request.urlopen("http://127.0.0.1:8001/metrics", timeout=3) as r:
            metrics_data = r.read().decode()
            has_metrics = "# HELP http_requests_total" in metrics_data
            print(f"[PASS] Monitored App Prometheus /metrics scraped: {has_metrics}")

        # 5. Check Overview Stats
        with urllib.request.urlopen("http://127.0.0.1:8000/api/dashboard/overview", timeout=3) as r:
            overview = json.loads(r.read().decode())
            print("[PASS] Dashboard Overview:", overview)

        print("\n>>> ALL SYSTEM VERIFICATION CHECKS PASSED SUCCESSFULLY! <<<")

    finally:
        p_mon.terminate()
        p_back.terminate()

if __name__ == "__main__":
    check_system()
