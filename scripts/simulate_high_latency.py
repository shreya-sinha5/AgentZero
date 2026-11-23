"""Simulate high latency failure scenario."""
import time
import urllib.request
import json

MONITORED_APP = "http://localhost:8001"
BACKEND_APP = "http://localhost:8000"

def run_simulation():
    print("[1] Injecting 2.0s latency into monitored-app...")
    fault_data = json.dumps({"latency_seconds": 2.0}).encode("utf-8")
    req = urllib.request.Request(
        f"{MONITORED_APP}/api/admin/inject-fault",
        data=fault_data,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            print("Response:", resp.read().decode())
    except Exception as e:
        print("Note: Monitored app not running locally or unreachable:", e)

    print("[2] Forwarding high-latency alert to AgentZero backend...")
    alert_payload = json.dumps({
        "service": "monitored-ecommerce",
        "metric": "response_latency",
        "observed_value": 2350.0,
        "baseline_value": 150.0,
        "severity": "critical",
        "description": "High API response latency detected across /api/products",
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
        print("Note: AgentZero backend not running locally or unreachable:", e)

if __name__ == "__main__":
    run_simulation()
