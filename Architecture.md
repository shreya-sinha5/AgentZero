# AgentZero — Architecture

**Version:** 1.0 · **Date:** 2026-11-23

---

## 1. Principles

1. **Deterministic detection, LLM reasoning.** Statistics and thresholds detect; LLMs interpret and coordinate.
2. **Centralised orchestration, shared state.** One supervisor, one incident state, structured messages. No all-to-all agent chatter.
3. **Patches, not edits.** Repair produces Git diffs on temporary branches.
4. **Prove it works.** No fix is deployed without independent testing and security validation.
5. **Least privilege.** Every tool call goes through a permission-controlled gateway.
6. **Evidence is data, not instructions.** Logs, code comments, and tickets are untrusted.
7. **Bounded everything.** Retries, timeouts, tokens, and escalation paths are explicit.
8. **Application-independent platform**, demonstrated first on an in-house e-commerce app.

## 2. Layered Overview

| Layer | Components | Purpose |
|---|---|---|
| Application | Demo e-commerce app, APIs, PostgreSQL, worker | System under observation |
| Observability | Prometheus, Loki, OpenTelemetry, Alertmanager, Grafana | Telemetry |
| Event processing | Alert receiver, incident processor, Redis Streams | Convert alerts to incidents |
| AI orchestration | LangGraph, 10 specialist agents + orchestrator | Investigate and resolve |
| Execution | Docker sandbox, Git, Pytest, Semgrep, Bandit, Trivy, GitHub Actions | Test and deploy repairs |
| Presentation | FastAPI, React + TypeScript dashboard | Transparency and control |

```
 Monitored App ──metrics/logs/traces──▶ Prometheus / Loki / OTel
                                              │
                                        Alertmanager
                                              ▼
                                     Alert Receiver (FastAPI)
                                              ▼
                              Incident Processor (dedupe, group, severity)
                                              ▼
                                       Redis Stream queue
                                              ▼
                               LangGraph Orchestrator ◀──▶ Shared Incident State
                                  │  │  │  │  │  │  │
                       Diagnostic RootCause DB Infra Repair Test Security Deploy Learning
                                              │
                                        Tool Gateway (allowlist, RBAC, audit)
                                  ┌──────────┼───────────┐
                              Sandbox      Git        Deployment
                                              ▼
                       Approval Service ──▶ Deployment ──▶ Health Verify ──▶ Rollback
                                              ▼
                          PostgreSQL + pgvector  ◀──▶  React Dashboard (WS/SSE)
```

## 3. Agent Catalogue

| Agent | Responsibility | Key tools | Permissions |
|---|---|---|---|
| **Orchestrator** | Workflow control, delegation, conflict handling, policy enforcement | Graph router, state store | Full workflow; cannot approve patches |
| **Monitoring** | Detect anomalies, emit incidents, initial severity | Metric query, anomaly detector | Read-only telemetry |
| **Diagnostic** | Gather and summarise evidence | Log search, trace analysis | Read-only |
| **Root Cause** | Rank hypotheses with evidence and disconfirming checks | Dependency graph, memory search | Read-only |
| **Database** | Slow queries, locks, pool exhaustion, indexing advice | DB inspector (`EXPLAIN`, stats views) | Read-only DB role; no DDL/DML |
| **Infrastructure** | CPU/memory/containers/network analysis | Container inspector, metric query | Read-only |
| **Repair** | Generate patch and rationale | Repo reader, Git manager (temp branch) | Write to temp branch only |
| **Testing** | Unit, integration, regression, perf comparison | Sandbox test runner | Sandbox only |
| **Security** | Scan patch; veto power | Bandit, Semgrep, Trivy, dep scanner | Read-only on patch |
| **Deployment** | Stage, smoke test, deploy, verify, rollback | Deployment manager | Acts only on approved artifacts |
| **Learning** | Index incidents, retrieve similar, post-incident reports | pgvector search | Write to knowledge base |

## 4. Orchestration (LangGraph)

### 4.1 Workflow
```
START → Incident → Diagnostic → RootCause
  RootCause: evidence insufficient? → MoreInvestigation → RootCause (bounded)
  → Repair → Testing
  Testing failed? → Repair (max N retries) else → Security
  Security failed? → Reject patch → Escalate
  → HumanApproval → Deployment(staging→prod) → HealthVerification
  Verification failed? → Rollback → Escalate/Re-investigate
  → Learning → END
```

### 4.2 Shared state
```python
class IncidentState(TypedDict):
    incident_id: str
    incident_data: dict
    logs: list
    metrics: dict
    traces: list
    diagnostic_report: dict
    root_cause_report: dict
    repair_patch: dict
    test_results: dict
    security_results: dict
    approval_status: str
    deployment_status: str
    rollback_required: bool
    execution_history: list
    retry_counters: dict      # per-node limits
    budget: dict              # tokens / cost / wall-clock
```

### 4.3 Dynamic routing
After diagnosis: low evidence → additional investigation; `database` → Database Agent; `infrastructure` → Infrastructure Agent; else → Root Cause. Confidence from an LLM is **validated against evidence completeness** and never trusted alone. Security Agent is activated only on suspicious behaviour or when a patch exists.

### 4.4 Disagreement handling
Conflicting findings (e.g. DB says query, Infra says memory) go to the Root Cause Agent to build a causal chain (bad deploy → expensive query → backlog → memory exhaustion).

### 4.5 Guards
Max retries per node, global investigation timeout, token budget, escalation to human on exhaustion. Checkpointing for resume after crash.

## 5. Agent Message Contract

All agents return typed (Pydantic) output.

```json
{
  "agent": "diagnostic_agent",
  "incident_id": "INC-1042",
  "status": "completed",
  "findings": [
    {"observation": "...", "evidence": "...", "timestamp": "..."}
  ],
  "recommendations": ["..."],
  "confidence": 0.91,
  "requires_escalation": false
}
```

Root Cause output additionally includes `hypotheses[]` with `evidence`, `confidence`, and `would_be_disproved_by`.

## 6. Tool Gateway

Single choke point between agents and the outside world.

- Per-agent **allowlist** of tools and argument schemas
- Scoped, short-lived credentials
- Resource limits (CPU, memory, time, output size)
- Output **redaction** of secrets before returning to the LLM
- **Audit log** entry per call (agent, tool, args hash, result hash, duration)
- Denies: arbitrary shell, production DB writes, permission changes, access to approval service

## 7. Execution Sandbox

- One ephemeral Docker container per validation run
- No production credentials, restricted network egress
- Repo checked out at patch branch; tests, perf harness, and scanners run inside
- Results returned as structured artifacts; container destroyed after

## 8. Deployment Pipeline

`Approved patch → build Docker image → staging deploy → smoke tests → production approval → canary → health verification → promote or rollback`

- Versioned, reversible artifacts; previous known-good always recorded
- DB changes must use backward-compatible migrations; rollback never relies on reversing ad-hoc SQL
- Rollback trigger: regression in latency, error rate, CPU/memory, health checks, DB latency

## 9. Data Architecture

### 9.1 Storage responsibilities
| Store | Holds |
|---|---|
| Prometheus | Metric time series |
| Loki | Logs |
| OTel backend | Traces |
| PostgreSQL | Incident metadata, executions, messages, repairs, approvals, deployments, references to telemetry |
| pgvector | Incident embeddings for similarity search |
| Redis | Event streams, ephemeral coordination, caches |

Do not store raw metric samples or every log line in PostgreSQL.

### 9.2 Core tables
Users, Services, Incidents, Metrics (summaries), Logs (incident-related excerpts), AgentExecutions, AgentMessages, RootCauses, Repairs, TestResults, SecurityResults, Approvals, Deployments, Rollbacks, KnowledgeBase.

### 9.3 Incident state machine
`DETECTED → INVESTIGATING → ROOT_CAUSE_IDENTIFIED → REPAIR_PROPOSED → VALIDATING → AWAITING_APPROVAL → DEPLOYING → VERIFYING → RESOLVED` plus `FAILED`, `REJECTED`, `ROLLED_BACK`, `ESCALATED`. Transitions enforced server-side in `incident_service.py`.

## 10. API Surface (FastAPI)

| Method | Endpoint | Function |
|---|---|---|
| GET | `/api/dashboard/overview` | Dashboard stats |
| GET | `/api/services` | Monitored services |
| GET | `/api/services/{id}/metrics` | Service metrics |
| POST | `/api/monitoring/alerts` | Alert ingestion |
| GET | `/api/incidents` | List incidents |
| GET | `/api/incidents/{id}` | Incident detail |
| POST | `/api/incidents/{id}/investigate` | Start investigation |
| GET | `/api/incidents/{id}/timeline` | Timeline |
| GET | `/api/agents` | List agents |
| GET | `/api/agents/{id}/executions` | Agent history |
| GET | `/api/repairs/{id}` | Repair detail |
| POST | `/api/repairs/{id}/approve` | Approve |
| POST | `/api/repairs/{id}/reject` | Reject |
| POST | `/api/repairs/{id}/test` | Run validation |
| POST | `/api/deployments` | Start approved deployment |
| POST | `/api/deployments/{id}/rollback` | Rollback |
| GET | `/api/knowledge/search` | Search past incidents |

Live updates via WebSocket or SSE (`/api/stream/incidents`, `/api/stream/agents`).

## 11. Frontend Architecture

React + TypeScript + Tailwind + Recharts. Pages: Dashboard, Monitoring, AgentControl, Incidents, IncidentDetails, RepairReview, Deployments, KnowledgeBase. State via hooks/contexts; services layer wraps REST and SSE. Light, clean SaaS theme.

## 12. Model Routing

| Task | Approach |
|---|---|
| Log classification | Deterministic rules or lightweight model |
| Root cause analysis | Strong reasoning model |
| Code repair / test generation | Coding-capable model |
| Security | Static analysis + AI review |
| Summaries | Lightweight model |

Start with one common model behind a provider-agnostic interface; vary later for cost/accuracy experiments.

## 13. Threat Model

| Threat | Control |
|---|---|
| Malicious generated code | Sandbox, Security Agent veto |
| Unauthorised prod change | Approval service + RBAC; Deployment Agent cannot bypass |
| Prompt injection via logs/code | Evidence wrapped as untrusted data; agents cannot change permissions or policy |
| Credential exposure | Secret manager, redaction |
| Compromised tool | Allowlist, scoped creds, audit |
| Runaway loops | Counters, timeouts, budgets |
| Self-approval | Repair and Approval roles separated |

**The Orchestrator enforces permissions independent of agent requests.**

## 14. Repository Layout

```
agentzero/
├── backend/app/{api,agents,orchestration,monitoring,tools,services,database,tests}
├── frontend/src/{components,pages,hooks,services,contexts,types}
├── monitored-app/{app,database,tests,Dockerfile,requirements.txt}
├── infrastructure/{docker-compose.yml,prometheus,grafana,loki,otel}
├── scripts/{simulate_high_latency,simulate_memory_leak,simulate_db_failure,simulate_api_failure}.py
├── docs/{architecture.md,api_documentation.md,incident_workflows.md}
├── PRD.md  Skills.md  phases.md  rules.md  memory.md  architecture.md
└── README.md
```

## 15. Technology Stack

| Component | Choice |
|---|---|
| Frontend | React, TypeScript, Tailwind, Recharts |
| Backend | Python, FastAPI, Pydantic |
| Orchestration | LangGraph |
| Database | PostgreSQL + pgvector |
| Queue/cache | Redis |
| Observability | Prometheus, Grafana, Loki, OpenTelemetry, Alertmanager |
| Execution | Docker, Git, GitHub Actions, Pytest |
| Security scanning | Semgrep, Bandit, Trivy |

Kubernetes is an advanced extension, not required for v1.

## 16. Deployment Topology (v1)

Single `docker-compose.yml`: monitored-app, postgres, redis, prometheus, grafana, loki, otel-collector, alertmanager, agentzero-backend, agentzero-frontend, sandbox-runner (ephemeral).
