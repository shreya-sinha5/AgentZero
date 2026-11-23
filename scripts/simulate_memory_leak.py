"""Simulate memory leak scenario."""
import time
import urllib.request
import json

MONITORED_APP = "http://localhost:8001"
BACKEND_APP = "http://localhost:8000"

def run_simulation():
    print("[1] Activating memory leak fault...")
    fault_data = json.dumps({"memory_leak_active": True}).encode("utf-8")
    req = urllib.request.Request(
        f"{MONITORED_APP}/api/admin/inject-fault",
        data=fault_data,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            print("Response:", resp.read().decode())
    except Exception as e:
        print("Note: Monitored app unreachable:", e)

    print("[2] Forwarding memory leak alert to AgentZero backend...")
    alert_payload = json.dumps({
        "service": "monitored-ecommerce",
        "metric": "memory_usage_bytes",
        "observed_value": 850000000.0,
        "baseline_value": 120000000.0,
        "severity": "critical",
        "description": "Memory consumption exceeding 85% threshold without release",
        "timestamp": time.time()
    }).encode("utf-8")

    req_alert = urllib.request.Request(
        f"{BACKEND_APP}/api/monitoring/alerts",
        data=alert_payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req_alert) as resp:
            print("Backend Alert Response:", resp.read().decode())
    except Exception as e:
        print("Note: AgentZero backend unreachable:", e)

if __name__ == "__main__":
    run_simulation()
