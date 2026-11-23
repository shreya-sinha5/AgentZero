"""Tests for Tool Gateway security, allowlists, and secret redaction."""
import pytest
from backend.app.tools.gateway import ToolGateway, ToolAccessDeniedError

def test_gateway_allowlisted_tool_execution():
    gw = ToolGateway()
    gw.register_tool("query_metrics", lambda query: {"result": "ok", "query": query})
    
    res = gw.execute("diagnostic_agent", "query_metrics", {"query": "rate(http_requests_total)"})
    assert res == {"result": "ok", "query": "rate(http_requests_total)"}
    
    assert len(gw.audit_log) == 1
    assert gw.audit_log[0]["status"] == "SUCCESS"
    assert gw.audit_log[0]["agent_id"] == "diagnostic_agent"

def test_gateway_unallowlisted_tool_denied():
    gw = ToolGateway()
    # diagnostic_agent is NOT allowed to call 'deploy_to_prod'
    gw.register_tool("deploy_to_prod", lambda version: {"deployed": version})
    
    with pytest.raises(ToolAccessDeniedError) as exc_info:
        gw.execute("diagnostic_agent", "deploy_to_prod", {"version": "v1.2"})
    
    assert "not in allowlist" in str(exc_info.value)
    assert len(gw.audit_log) == 1
    assert gw.audit_log[0]["status"] == "DENIED"

def test_gateway_secret_redaction():
    gw = ToolGateway()
    gw.register_tool("search_logs", lambda log_filter: {
        "logs": [f"Auth token bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xyz and password: supersecret123"]
    })
    
    result = gw.execute("diagnostic_agent", "search_logs", {"log_filter": "auth"})
    output_text = str(result)
    assert "supersecret123" not in output_text
    assert "[REDACTED]" in output_text
