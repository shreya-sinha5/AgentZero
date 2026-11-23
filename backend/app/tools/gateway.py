"""Tool Gateway enforcing least-privilege access, allowlists, redaction, and audit logging."""
import hashlib
import json
import re
import time
from typing import Any, Callable, Dict, List, Optional

# Secret redaction patterns
SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|password|secret|token|bearer)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{8,})['\"]?"),
    re.compile(r"(?i)bearer\s+([a-zA-Z0-9_\-\.]{15,})")
]

class ToolAccessDeniedError(PermissionError):
    """Raised when an agent requests an unallowed tool or invalid operation."""
    pass

class ToolGateway:
    def __init__(self):
        # Per-agent allowlists per Architecture section 6 & Skills.md
        self.allowlists: Dict[str, List[str]] = {
            "orchestrator": ["get_incident_state", "update_incident_state", "route_to_agent"],
            "diagnostic_agent": ["query_metrics", "search_logs", "analyze_traces"],
            "root_cause_agent": ["query_metrics", "search_knowledge_base", "get_dependency_graph"],
            "database_agent": ["explain_query", "get_db_stats"],
            "infrastructure_agent": ["get_container_stats", "get_host_metrics"],
            "repair_agent": ["read_source_file", "create_temp_branch", "generate_git_patch"],
            "testing_agent": ["run_sandbox_tests"],
            "security_agent": ["run_bandit_scan", "run_semgrep_scan", "run_dependency_scan"],
            "deployment_agent": ["deploy_to_staging", "deploy_to_prod", "trigger_rollback"],
            "learning_agent": ["index_incident", "search_similar_incidents"],
        }
        self.registry: Dict[str, Callable] = {}
        self.audit_log: List[Dict[str, Any]] = []

    def register_tool(self, name: str, handler: Callable):
        self.registry[name] = handler

    def redact_data(self, data: Any) -> Any:
        """Recursively redact tokens, credentials, and secrets from dict, list, or string data."""
        if isinstance(data, str):
            s = re.sub(r"(?i)(api[_-]?key|password|secret|token)\s*[:=]\s*['\"]?[a-zA-Z0-9_\-\.]+['\"]?", r"\1: [REDACTED]", data)
            return re.sub(r"(?i)\bbearer\s+[a-zA-Z0-9_\-\.]+", "bearer [REDACTED]", s)
        elif isinstance(data, dict):
            return {k: self.redact_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.redact_data(item) for item in data]
        return data

    def execute(self, agent_id: str, tool_name: str, args: Optional[Dict[str, Any]] = None) -> Any:
        args = args or {}
        start_time = time.time()
        
        # 1. Authority and permission check
        allowed_tools = self.allowlists.get(agent_id, [])
        if tool_name not in allowed_tools:
            record = {
                "timestamp": start_time,
                "agent_id": agent_id,
                "tool_name": tool_name,
                "status": "DENIED",
                "duration": time.time() - start_time,
                "reason": f"Tool '{tool_name}' not in allowlist for agent '{agent_id}'"
            }
            self.audit_log.append(record)
            raise ToolAccessDeniedError(record["reason"])

        # 2. Handler lookup
        handler = self.registry.get(tool_name)
        if not handler:
            raise KeyError(f"No registered handler for tool '{tool_name}'")

        # 3. Execution
        try:
            raw_result = handler(**args)
            duration = time.time() - start_time
            clean_result = self.redact_data(raw_result)
            
            args_hash = hashlib.sha256(json.dumps(args, sort_keys=True, default=str).encode()).hexdigest()[:12]
            res_hash = hashlib.sha256(json.dumps(clean_result, sort_keys=True, default=str).encode()).hexdigest()[:12]

            self.audit_log.append({
                "timestamp": start_time,
                "agent_id": agent_id,
                "tool_name": tool_name,
                "args_hash": args_hash,
                "result_hash": res_hash,
                "status": "SUCCESS",
                "duration": duration
            })
            return clean_result
        except Exception as ex:
            self.audit_log.append({
                "timestamp": start_time,
                "agent_id": agent_id,
                "tool_name": tool_name,
                "status": "FAILED",
                "duration": time.time() - start_time,
                "error": str(ex)
            })
            raise

gateway = ToolGateway()
