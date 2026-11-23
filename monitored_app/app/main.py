"""Demo E-Commerce Service with deterministic Prometheus metrics."""
import asyncio
import os
import sys
import time
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Response, Request
from pydantic import BaseModel
from .database import db

app = FastAPI(title="AgentZero Monitored E-Commerce Demo", version="1.0.0")

# Telemetry counters & gauges
request_counts: Dict[str, int] = {}
request_latencies: Dict[str, List[float]] = {}
error_counts: Dict[str, int] = {}
leaked_memory_blocks: List[bytearray] = []

# Fault injection toggles
fault_config = {
    "latency_seconds": 0.0,
    "error_rate": 0.0,
    "db_slow_query": False,
    "db_pool_exhausted": False,
    "memory_leak_active": False,
}

class FaultInjectionRequest(BaseModel):
    latency_seconds: Optional[float] = 0.0
    error_rate: Optional[float] = 0.0
    db_slow_query: Optional[bool] = False
    db_pool_exhausted: Optional[bool] = False
    memory_leak_active: Optional[bool] = False

class CartItemRequest(BaseModel):
    user_id: str
    product_id: int
    quantity: int = 1

class CheckoutRequest(BaseModel):
    user_id: str
    amount: float

@app.middleware("http")
async def telemetry_middleware(request: Request, call_next):
    start_time = time.time()
    endpoint = request.url.path

    # Apply injected latency if configured
    if fault_config["latency_seconds"] > 0:
        await asyncio.sleep(fault_config["latency_seconds"])

    # Apply injected memory leak
    if fault_config["memory_leak_active"]:
        leaked_memory_blocks.append(bytearray(2 * 1024 * 1024))  # 2MB per request

    response = await call_next(request)
    duration = time.time() - start_time

    # Record telemetry
    status_str = str(response.status_code)
    key = f"{request.method}_{endpoint}_{status_str}"
    request_counts[key] = request_counts.get(key, 0) + 1
    
    lat_key = f"{request.method}_{endpoint}"
    if lat_key not in request_latencies:
        request_latencies[lat_key] = []
    # Keep last 50 latencies for moving average
    request_latencies[lat_key].append(duration)
    if len(request_latencies[lat_key]) > 50:
        request_latencies[lat_key].pop(0)

    if response.status_code >= 400:
        error_counts[endpoint] = error_counts.get(endpoint, 0) + 1

    return response

@app.get("/health")
def health_check():
    if fault_config["db_pool_exhausted"]:
        raise HTTPException(status_code=503, detail="Database connection pool exhausted")
    return {
        "status": "healthy",
        "service": "monitored-ecommerce",
        "timestamp": time.time(),
        "database": "connected"
    }

@app.get("/api/products")
def get_products():
    if fault_config["db_slow_query"]:
        time.sleep(1.5)  # simulate full-table unindexed scan
    return {"products": db.list_products()}

@app.get("/api/products/{product_id}")
def get_product(product_id: int):
    product = db.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.post("/api/cart/items")
def add_cart_item(item: CartItemRequest):
    return db.add_to_cart(item.user_id, item.product_id, item.quantity)

@app.get("/api/cart")
def view_cart(user_id: str):
    return {"user_id": user_id, "items": db.get_cart(user_id)}

@app.post("/api/orders")
def checkout_order(order: CheckoutRequest):
    if fault_config["error_rate"] > 0:
        # Simulate payment gateway failure
        raise HTTPException(status_code=502, detail="Payment gateway timeout / failure")
    return db.create_order(order.user_id, order.amount)

@app.post("/api/admin/inject-fault")
def inject_fault(fault: FaultInjectionRequest):
    fault_config.update(fault.model_dump(exclude_unset=True))
    return {"status": "updated", "current_faults": fault_config}

@app.post("/api/admin/reset-faults")
def reset_faults():
    for k in fault_config:
        if isinstance(fault_config[k], bool):
            fault_config[k] = False
        else:
            fault_config[k] = 0.0
    leaked_memory_blocks.clear()
    return {"status": "reset", "current_faults": fault_config}

@app.get("/api/admin/status")
def admin_status():
    return {
        "faults": fault_config,
        "leaked_blocks_count": len(leaked_memory_blocks),
        "total_requests": sum(request_counts.values())
    }

@app.get("/metrics")
def prometheus_metrics():
    """Deterministic Prometheus text exposition."""
    lines = [
        "# HELP http_requests_total Total number of HTTP requests.",
        "# TYPE http_requests_total counter"
    ]
    for key, count in request_counts.items():
        parts = key.split("_")
        method = parts[0]
        status = parts[-1]
        endpoint = "_".join(parts[1:-1])
        lines.append(f'http_requests_total{{method="{method}",endpoint="{endpoint}",status="{status}"}} {count}')

    lines.extend([
        "# HELP http_request_duration_seconds Average latency of HTTP requests.",
        "# TYPE http_request_duration_seconds gauge"
    ])
    for endpoint, samples in request_latencies.items():
        avg_lat = sum(samples) / len(samples) if samples else 0.0
        lines.append(f'http_request_duration_seconds{{endpoint="{endpoint}"}} {avg_lat:.4f}')

    lines.extend([
        "# HELP db_connections Active database connections.",
        "# TYPE db_connections gauge",
        f"db_connections {db.active_connections}",
        "# HELP memory_leaked_bytes Simulated leaked memory blocks.",
        "# TYPE memory_leaked_bytes gauge",
        f"memory_leaked_bytes {len(leaked_memory_blocks) * 2 * 1024 * 1024}"
    ])

    return Response(content="\n".join(lines) + "\n", media_type="text/plain; version=0.0.4")
