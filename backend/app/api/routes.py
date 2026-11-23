"""FastAPI REST API routes per Architecture Section 10."""
import time
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..models import (
    AlertPayload, Incident, IncidentStatus, ApprovalDecision, DeploymentRecord
)
from ..services.incident_service import incident_service, InvalidStateTransitionError

router = APIRouter()

class ApprovalRequestBody(BaseModel):
    approver: str
    decision: str  # "approved" or "rejected"
    comments: Optional[str] = ""

class DeploymentRequestBody(BaseModel):
    incident_id: str
    version: str
    target: str = "staging"

class TransitionRequestBody(BaseModel):
    new_status: IncidentStatus

@router.get("/dashboard/overview")
def get_dashboard_overview():
    incidents = incident_service.list_incidents()
    active = [i for i in incidents if i.status not in [IncidentStatus.RESOLVED, IncidentStatus.REJECTED]]
    resolved = [i for i in incidents if i.status == IncidentStatus.RESOLVED]
    
    return {
        "total_incidents": len(incidents),
        "active_incidents": len(active),
        "resolved_incidents": len(resolved),
        "system_status": "degraded" if active else "healthy",
        "mttd_seconds": 12.5,
        "mttr_seconds": 180.0
    }

@router.post("/monitoring/alerts")
def ingest_alert(alert: AlertPayload):
    incident = incident_service.process_alert(alert)
    return {
        "status": "received",
        "incident_id": incident.incident_id,
        "incident_status": incident.status,
        "alerts_count": len(incident.alerts)
    }

@router.get("/incidents", response_model=List[Incident])
def list_incidents(status: Optional[IncidentStatus] = Query(None)):
    filter_status = status if isinstance(status, IncidentStatus) else None
    return incident_service.list_incidents(status=filter_status)

@router.get("/incidents/{incident_id}", response_model=Incident)
def get_incident(incident_id: str):
    inc = incident_service.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    return inc

@router.post("/incidents/{incident_id}/transition")
def transition_incident(incident_id: str, body: TransitionRequestBody):
    try:
        return incident_service.transition_incident(incident_id, body.new_status)
    except KeyError:
        raise HTTPException(status_code=404, detail="Incident not found")
    except InvalidStateTransitionError as ex:
        raise HTTPException(status_code=400, detail=str(ex))

@router.post("/repairs/{incident_id}/approve")
def approve_repair(incident_id: str, body: ApprovalRequestBody):
    try:
        return incident_service.record_approval(
            incident_id=incident_id,
            approver=body.approver,
            decision="approved",
            comments=body.comments or ""
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Incident not found")
    except InvalidStateTransitionError as ex:
        raise HTTPException(status_code=400, detail=str(ex))

@router.post("/repairs/{incident_id}/reject")
def reject_repair(incident_id: str, body: ApprovalRequestBody):
    try:
        return incident_service.record_approval(
            incident_id=incident_id,
            approver=body.approver,
            decision="rejected",
            comments=body.comments or ""
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Incident not found")
    except InvalidStateTransitionError as ex:
        raise HTTPException(status_code=400, detail=str(ex))

@router.post("/deployments")
def trigger_deployment(body: DeploymentRequestBody):
    inc = incident_service.get_incident(body.incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    if inc.status != IncidentStatus.DEPLOYING:
        raise HTTPException(status_code=400, detail=f"Cannot deploy when incident is in '{inc.status}' state")
    
    return incident_service.record_deployment(
        incident_id=body.incident_id,
        version=body.version,
        status="deploying"
    )

@router.post("/deployments/{incident_id}/rollback")
def rollback_deployment(incident_id: str):
    try:
        return incident_service.record_deployment(
            incident_id=incident_id,
            version="previous-stable",
            status="rolled_back",
            rolled_back=True
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Incident not found")
    except InvalidStateTransitionError as ex:
        raise HTTPException(status_code=400, detail=str(ex))
