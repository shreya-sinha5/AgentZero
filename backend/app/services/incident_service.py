"""Incident lifecycle state machine and grouping service."""
import time
from typing import Dict, List, Optional
from ..models import (
    Incident, IncidentStatus, IncidentSeverity, FailureType,
    AlertPayload, ApprovalDecision, DeploymentRecord
)

ALLOWED_TRANSITIONS: Dict[IncidentStatus, List[IncidentStatus]] = {
    IncidentStatus.DETECTED: [
        IncidentStatus.INVESTIGATING,
        IncidentStatus.ESCALATED,
        IncidentStatus.RESOLVED,
    ],
    IncidentStatus.INVESTIGATING: [
        IncidentStatus.ROOT_CAUSE_IDENTIFIED,
        IncidentStatus.ESCALATED,
    ],
    IncidentStatus.ROOT_CAUSE_IDENTIFIED: [
        IncidentStatus.REPAIR_PROPOSED,
        IncidentStatus.ESCALATED,
    ],
    IncidentStatus.REPAIR_PROPOSED: [
        IncidentStatus.VALIDATING,
        IncidentStatus.ESCALATED,
    ],
    IncidentStatus.VALIDATING: [
        IncidentStatus.AWAITING_APPROVAL,
        IncidentStatus.REPAIR_PROPOSED,  # retry on test failure
        IncidentStatus.REJECTED,
        IncidentStatus.ESCALATED,
    ],
    IncidentStatus.AWAITING_APPROVAL: [
        IncidentStatus.DEPLOYING,
        IncidentStatus.REJECTED,
        IncidentStatus.ESCALATED,
    ],
    IncidentStatus.DEPLOYING: [
        IncidentStatus.VERIFYING,
        IncidentStatus.ROLLED_BACK,
        IncidentStatus.FAILED,
    ],
    IncidentStatus.VERIFYING: [
        IncidentStatus.RESOLVED,
        IncidentStatus.ROLLED_BACK,
        IncidentStatus.ESCALATED,
    ],
    IncidentStatus.ROLLED_BACK: [
        IncidentStatus.INVESTIGATING,
        IncidentStatus.ESCALATED,
    ],
    # Terminal states
    IncidentStatus.RESOLVED: [],
    IncidentStatus.FAILED: [],
    IncidentStatus.REJECTED: [],
    IncidentStatus.ESCALATED: [],
}

class InvalidStateTransitionError(ValueError):
    """Raised when an illegal incident status transition is attempted."""
    pass

class IncidentService:
    def __init__(self):
        self._incidents: Dict[str, Incident] = {}
        self._next_id: int = 1001
        self._dedupe_window_seconds: float = 600.0  # 10 minutes

    def process_alert(self, alert: AlertPayload) -> Incident:
        """Deduplicate/group incoming alerts into an active incident or create a new one."""
        now = time.time()
        
        # Check for existing active incident with same service & metric
        for inc in self._incidents.values():
            if inc.service == alert.service and inc.status not in [
                IncidentStatus.RESOLVED, IncidentStatus.FAILED, IncidentStatus.REJECTED
            ]:
                # Check if recent alert with same metric exists
                for prev in inc.alerts:
                    if prev.metric == alert.metric and (now - prev.timestamp) < self._dedupe_window_seconds:
                        inc.alerts.append(alert)
                        inc.updated_at = now
                        return inc

        # Create new incident
        inc_id = f"INC-{self._next_id}"
        self._next_id += 1
        
        # Determine initial failure type from metric
        failure_type = FailureType.APPLICATION
        if "db" in alert.metric.lower() or "database" in alert.metric.lower():
            failure_type = FailureType.DATABASE
        elif "memory" in alert.metric.lower() or "cpu" in alert.metric.lower() or "host" in alert.metric.lower():
            failure_type = FailureType.INFRASTRUCTURE

        incident = Incident(
            incident_id=inc_id,
            service=alert.service,
            title=f"Anomaly detected on {alert.service}: {alert.metric} ({alert.observed_value} vs {alert.baseline_value})",
            status=IncidentStatus.DETECTED,
            severity=alert.severity,
            failure_type=failure_type,
            created_at=now,
            updated_at=now,
            alerts=[alert]
        )
        self._incidents[inc_id] = incident
        return incident

    def get_incident(self, incident_id: str) -> Optional[Incident]:
        return self._incidents.get(incident_id)

    def list_incidents(self, status: Optional[IncidentStatus] = None) -> List[Incident]:
        if status:
            return [inc for inc in self._incidents.values() if inc.status == status]
        return list(self._incidents.values())

    def transition_incident(self, incident_id: str, new_status: IncidentStatus) -> Incident:
        """Strictly validate and perform an incident state transition."""
        incident = self._incidents.get(incident_id)
        if not incident:
            raise KeyError(f"Incident '{incident_id}' not found")

        current = incident.status
        allowed = ALLOWED_TRANSITIONS.get(current, [])
        if new_status not in allowed:
            raise InvalidStateTransitionError(
                f"Illegal transition from '{current}' to '{new_status}'. Allowed: {allowed}"
            )

        incident.status = new_status
        incident.updated_at = time.time()
        return incident

    def record_approval(self, incident_id: str, approver: str, decision: str, comments: str = "") -> Incident:
        incident = self._incidents.get(incident_id)
        if not incident:
            raise KeyError(f"Incident '{incident_id}' not found")

        record = ApprovalDecision(approver=approver, decision=decision, comments=comments)
        incident.approvals.append(record)
        
        if decision.lower() == "approved":
            return self.transition_incident(incident_id, IncidentStatus.DEPLOYING)
        else:
            return self.transition_incident(incident_id, IncidentStatus.REJECTED)

    def record_deployment(self, incident_id: str, version: str, status: str, rolled_back: bool = False) -> Incident:
        incident = self._incidents.get(incident_id)
        if not incident:
            raise KeyError(f"Incident '{incident_id}' not found")

        incident.deployment = DeploymentRecord(version=version, status=status, rolled_back=rolled_back)
        if rolled_back:
            return self.transition_incident(incident_id, IncidentStatus.ROLLED_BACK)
        elif status == "verified":
            if incident.status == IncidentStatus.DEPLOYING:
                self.transition_incident(incident_id, IncidentStatus.VERIFYING)
            return self.transition_incident(incident_id, IncidentStatus.RESOLVED)
        elif status == "deploying":
            return self.transition_incident(incident_id, IncidentStatus.VERIFYING)
        return incident

incident_service = IncidentService()
