"""Data contracts and schemas for AgentZero platform."""
from enum import Enum
import time
from typing import Dict, List, Optional, Any, TypedDict
from pydantic import BaseModel, Field

class IncidentStatus(str, Enum):
    DETECTED = "DETECTED"
    INVESTIGATING = "INVESTIGATING"
    ROOT_CAUSE_IDENTIFIED = "ROOT_CAUSE_IDENTIFIED"
    REPAIR_PROPOSED = "REPAIR_PROPOSED"
    VALIDATING = "VALIDATING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    DEPLOYING = "DEPLOYING"
    VERIFYING = "VERIFYING"
    RESOLVED = "RESOLVED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"
    ROLLED_BACK = "ROLLED_BACK"
    ESCALATED = "ESCALATED"

class IncidentSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class FailureType(str, Enum):
    DATABASE = "database"
    INFRASTRUCTURE = "infrastructure"
    APPLICATION = "application"
    UNKNOWN = "unknown"

class AlertPayload(BaseModel):
    service: str
    metric: str
    observed_value: float
    baseline_value: float
    severity: IncidentSeverity = IncidentSeverity.HIGH
    description: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)

class Finding(BaseModel):
    observation: str
    evidence: str
    timestamp: float = Field(default_factory=time.time)

class DiagnosticReport(BaseModel):
    agent: str = "diagnostic_agent"
    incident_id: str
    status: str = "completed"
    findings: List[Finding] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    confidence: float = 0.0
    requires_escalation: bool = False
    failure_type: FailureType = FailureType.UNKNOWN

class RootCauseHypothesis(BaseModel):
    cause: str
    evidence: List[str] = Field(default_factory=list)
    confidence: float
    would_be_disproved_by: str

class RootCauseReport(BaseModel):
    agent: str = "root_cause_agent"
    incident_id: str
    hypotheses: List[RootCauseHypothesis] = Field(default_factory=list)
    selected: str
    causal_chain: List[str] = Field(default_factory=list)
    confidence: float

class RepairPatch(BaseModel):
    agent: str = "repair_agent"
    incident_id: str
    branch: str
    diff: str
    rationale: str
    potential_side_effects: List[str] = Field(default_factory=list)

class TestResults(BaseModel):
    agent: str = "testing_agent"
    incident_id: str
    verdict: str  # "pass" or "fail"
    unit_tests: Dict[str, Any] = Field(default_factory=dict)
    integration_tests: Dict[str, Any] = Field(default_factory=dict)
    perf_delta: Optional[str] = None

class SecurityResults(BaseModel):
    agent: str = "security_agent"
    incident_id: str
    verdict: str  # "pass" or "veto"
    vulnerabilities: List[str] = Field(default_factory=list)
    veto_deployment: bool = False

class ApprovalDecision(BaseModel):
    approver: str
    decision: str  # "approved" or "rejected"
    comments: Optional[str] = ""
    timestamp: float = Field(default_factory=time.time)

class DeploymentRecord(BaseModel):
    version: str
    status: str  # "staging", "prod", "rolled_back", "failed"
    rolled_back: bool = False
    timestamp: float = Field(default_factory=time.time)

class Incident(BaseModel):
    incident_id: str
    service: str
    title: str
    status: IncidentStatus = IncidentStatus.DETECTED
    severity: IncidentSeverity = IncidentSeverity.HIGH
    failure_type: FailureType = FailureType.UNKNOWN
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    alerts: List[AlertPayload] = Field(default_factory=list)
    diagnostic_report: Optional[DiagnosticReport] = None
    root_cause_report: Optional[RootCauseReport] = None
    repair_patch: Optional[RepairPatch] = None
    test_results: Optional[TestResults] = None
    security_results: Optional[SecurityResults] = None
    approvals: List[ApprovalDecision] = Field(default_factory=list)
    deployment: Optional[DeploymentRecord] = None

# LangGraph shared state representation
class IncidentState(TypedDict, total=False):
    incident_id: str
    incident_data: Dict[str, Any]
    logs: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    traces: List[Dict[str, Any]]
    diagnostic_report: Optional[Dict[str, Any]]
    root_cause_report: Optional[Dict[str, Any]]
    repair_patch: Optional[Dict[str, Any]]
    test_results: Optional[Dict[str, Any]]
    security_results: Optional[Dict[str, Any]]
    approval_status: str
    deployment_status: str
    rollback_required: bool
    execution_history: List[Dict[str, Any]]
    retry_counters: Dict[str, int]
    budget: Dict[str, Any]
