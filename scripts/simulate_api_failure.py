"""Simulate 500 payment gateway error scenario."""
import time
import urllib.request
import json

MONITORED_APP = "http://localhost:8001"
BACKEND_APP = "http://localhost:8000"

def run_simulation():
    print("[1] Injecting payment API error rate fault...")
    fault_data = json.dumps({"error_rate": 1.0}).encode("utf-8")
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

    print("[2] Forwarding 5xx error rate alert to AgentZero backend...")
    alert_payload = json.dumps({
        "service": "monitored-ecommerce",
        "metric": "service_5xx_rate",
        "observed_value": 0.45,
        "baseline_value": 0.001,
        "severity": "critical",
        "description": "Payment gateway timeout errors spiking above threshold",
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
