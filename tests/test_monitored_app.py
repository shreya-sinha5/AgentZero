"""Tests for demo monitored e-commerce app and telemetry metrics."""
import pytest
from fastapi.testclient import TestClient
from monitored_app.app.main import app, fault_config, leaked_memory_blocks

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_faults():
    client.post("/api/admin/reset-faults")
    yield
    client.post("/api/admin/reset-faults")

def test_health_check_healthy():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "monitored-ecommerce"

def test_product_catalog_and_cart():
    # 1. List products
    resp = client.get("/api/products")
    assert resp.status_code == 200
    products = resp.json()["products"]
    assert len(products) >= 1
    first_id = products[0]["id"]

    # 2. Add to cart
    resp = client.post("/api/cart/items", json={"user_id": "test_user_1", "product_id": first_id, "quantity": 2})
    assert resp.status_code == 200

    # 3. View cart
    resp = client.get("/api/cart?user_id=test_user_1")
    assert resp.status_code == 200
    cart_items = resp.json()["items"]
    assert len(cart_items) == 1
    assert cart_items[0]["product_id"] == first_id

    # 4. Checkout order
    resp = client.post("/api/orders", json={"user_id": "test_user_1", "amount": 2599.98})
    assert resp.status_code == 200
    order = resp.json()
    assert order["status"] == "COMPLETED"

def test_prometheus_metrics_exposition():
    # Make a few requests
    client.get("/api/products")
    client.get("/health")

    resp = client.get("/metrics")
    assert resp.status_code == 200
    content = resp.text
    assert "# HELP http_requests_total" in content
    assert "http_requests_total" in content
    assert "db_connections" in content
    assert "memory_leaked_bytes" in content

def test_fault_injection_db_exhaustion():
    resp = client.post("/api/admin/inject-fault", json={"db_pool_exhausted": True})
    assert resp.status_code == 200
    
    # Health check should now fail with 503
    resp = client.get("/health")
    assert resp.status_code == 503
