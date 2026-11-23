"""Tests for demo monitored e-commerce app logic and metrics."""
import pytest
from monitored_app.app.main import (
    health_check,
    get_products,
    get_product,
    add_cart_item,
    view_cart,
    checkout_order,
    inject_fault,
    reset_faults,
    prometheus_metrics,
    CartItemRequest,
    CheckoutRequest,
    FaultInjectionRequest,
    fault_config
)
from fastapi import HTTPException

@pytest.fixture(autouse=True)
def cleanup_faults():
    reset_faults()
    yield
    reset_faults()

def test_health_check_healthy():
    res = health_check()
    assert res["status"] == "healthy"
    assert res["service"] == "monitored-ecommerce"

def test_product_catalog_and_cart():
    # 1. List products
    catalog = get_products()
    assert len(catalog["products"]) >= 1
    first_id = catalog["products"][0]["id"]

    # 2. Get single product
    product = get_product(first_id)
    assert product["id"] == first_id

    # 3. Add to cart
    cart_item = add_cart_item(CartItemRequest(user_id="test_user_1", product_id=first_id, quantity=2))
    assert cart_item["product_id"] == first_id

    # 4. View cart
    cart = view_cart("test_user_1")
    assert len(cart["items"]) == 1

    # 5. Checkout
    order = checkout_order(CheckoutRequest(user_id="test_user_1", amount=1299.99))
    assert order["status"] == "COMPLETED"

def test_prometheus_metrics_exposition():
    resp = prometheus_metrics()
    content = resp.body.decode("utf-8")
    assert "# HELP http_requests_total" in content
    assert "db_connections" in content
    assert "memory_leaked_bytes" in content

def test_fault_injection_db_exhaustion():
    inject_fault(FaultInjectionRequest(db_pool_exhausted=True))
    with pytest.raises(HTTPException) as exc:
        health_check()
    assert exc.value.status_code == 503
