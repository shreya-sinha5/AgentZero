# AgentZero — Product Requirements Document (PRD)

**Version:** 1.0 · **Date:** 2026-11-23 · **Status:** Draft for approval
**Category:** Advanced AI + Multi-Agent Systems / Software Reliability Engineering

---

## 1. Vision

A software system should not only tell developers when something goes wrong. It should understand what went wrong, determine why, develop a fix, validate it, and recover itself safely, with a human approving risky actions.

AgentZero is an autonomous multi-agent platform that behaves like a small Site Reliability Engineering (SRE) team: it monitors an application, detects anomalies, investigates root causes, generates patches, tests them in isolation, scans them for security issues, and deploys them under controlled approval, with automatic rollback.

## 2. Problem Statement

Modern applications are made of interconnected services, databases, APIs, and workers. One failure cascades (slow query → timeouts → retries → load → outage). Traditional monitoring detects and alerts, but diagnosis and recovery still need heavy human effort. Rule-based auto-recovery cannot reason about complex, interconnected failures.

## 3. Goals and Non-Goals

### Goals
1. Continuously monitor application health and infrastructure.
2. Detect anomalies before they become critical failures.
3. Correlate logs, metrics, and traces.
4. Identify probable root causes with supporting evidence (not just symptoms).
5. Generate context-aware code or configuration fixes as Git patches.
6. Validate fixes in an isolated sandbox (tests, performance, security).
7. Deploy approved fixes through staging with health verification.
8. Roll back failed deployments automatically.
9. Keep a complete audit trail of every agent decision and action.
10. Learn from historical incidents via controlled retrieval.
11. **Demonstrate measurably** whether multi-agent orchestration beats single-agent and rule-based approaches.

### Non-Goals (v1)
- Inventing self-healing; the project differentiates on the evidence-driven repair loop and its evaluation.
- Fully autonomous production deploys (Level 3 is an extension).
- Kubernetes support (advanced extension).
- Training or fine-tuning LLMs on incident data (retrieval only).
- Monitoring arbitrary third-party production apps in v1 (start with own demo app, design the platform to be application-independent).

## 4. Target Users and Personas

| Persona | Needs |
|---|---|
| **On-call developer** | Fast, evidence-backed root cause; reviewable patch; one-click approve/reject |
| **SRE / platform engineer** | Policy control, audit trail, rollback confidence, agent transparency |
| **Engineering manager** | Incident metrics (MTTD, MTTR), cost per incident |
| **Academic evaluator / researcher** | Reproducible failure scenarios and comparative results |

## 5. Scope by Release

| Release | Contents | Goal |
|---|---|---|
| **R1 — Functional MVP** | Demo e-commerce app, Prometheus monitoring, incident detection, Orchestrator, Diagnostic + Root Cause + Repair + Testing agents, human-approved patch application, basic React dashboard | Detect, diagnose, validate a repair |
| **R2 — Advanced system** | Dynamic delegation, Database + Infrastructure agents, Security agent, Docker sandbox, Deployment agent, rollback, incident memory, live agent visualisation | Complete controlled self-healing |
| **R3 — Research extensions** | Adaptive agent selection, multi-agent debate, historical learning, cascading-failure analysis, model routing/cost optimisation, Kubernetes, benchmarking | Research contribution |

## 6. Functional Requirements

Priority: **P0** must-have (R1), **P1** should-have (R2), **P2** nice-to-have (R3).

### 6.1 Monitoring and Detection
| ID | Requirement | Pri |
|---|---|---|
| FR-01 | Ingest metrics (CPU, memory, disk, latency, error rate, DB connections, throughput, container health) via Prometheus | P0 |
| FR-02 | Detect anomalies with deterministic methods (thresholds, moving averages, Isolation Forest); the LLM must not be the sole numeric detector | P0 |
| FR-03 | Receive alerts via `POST /api/monitoring/alerts`, deduplicate, group, assign incident IDs and severity | P0 |
| FR-04 | Ingest logs (Loki) and traces (OpenTelemetry) | P1 |

### 6.2 Investigation
| ID | Requirement | Pri |
|---|---|---|
| FR-10 | Diagnostic Agent retrieves logs/traces around the incident and summarises evidence | P0 |
| FR-11 | Root Cause Agent produces ranked hypotheses with evidence, confidence, and disconfirming evidence | P0 |
| FR-12 | Database Agent detects slow queries, pool exhaustion, locks, missing indexes | P1 |
| FR-13 | Infrastructure Agent detects leaks, crashes, resource exhaustion, restart loops | P1 |
| FR-14 | Orchestrator dynamically selects agents based on failure type and confidence | P1 |
| FR-15 | Conflicting agent findings are adjudicated by the Root Cause Agent | P1 |

### 6.3 Repair and Validation
| ID | Requirement | Pri |
|---|---|---|
| FR-20 | Repair Agent outputs a Git diff on a temporary branch, never edits production directly | P0 |
| FR-21 | Testing Agent runs unit, integration, regression, and before/after performance tests in an isolated container | P0 |
| FR-22 | Failed tests loop back to Repair Agent with errors, bounded by max retries | P0 |
| FR-23 | Security Agent runs Bandit, Semgrep, Trivy, dependency scans; can veto deployment | P1 |
| FR-24 | Repair Agent cannot approve its own patch | P0 |

### 6.4 Approval and Deployment
| ID | Requirement | Pri |
|---|---|---|
| FR-30 | Human approval gateway (approve / reject / request revision) with recorded approver | P0 |
| FR-31 | Deploy to staging, run smoke tests, then production after approval | P1 |
| FR-32 | Post-deploy health verification (latency, error rate, CPU, memory, DB latency) | P1 |
| FR-33 | Automatic rollback to last known-good version on failed verification | P1 |
| FR-34 | Level 1 safe operational recovery (restart worker, drain unhealthy instance) under explicit policy | P1 |

### 6.5 Memory and Learning
| ID | Requirement | Pri |
|---|---|---|
| FR-40 | Store resolved incidents, root causes, fixes, outcomes | P1 |
| FR-41 | Retrieve similar past incidents (pgvector) during investigation | P1 |
| FR-42 | Generate post-incident reports and recurring-pattern suggestions | P2 |

### 6.6 Dashboard (React)
| ID | Requirement | Pri |
|---|---|---|
| FR-50 | Overview: system health, active/resolved incidents, agent activity | P0 |
| FR-51 | Live monitoring page (per-service graphs, alerts) | P1 |
| FR-52 | Agent control centre: states, tasks, tool calls, duration, tokens, errors, delegation history | P1 |
| FR-53 | Incident investigation page with timeline, evidence, hypotheses, proposed repair | P0 |
| FR-54 | Repair review page: side-by-side diff, tests, security, risk, approve/reject | P0 |
| FR-55 | Deployment centre with approval records and rollback history | P1 |
| FR-56 | Incident knowledge base search | P1 |
| FR-57 | Real-time updates via WebSocket/SSE | P1 |

### 6.7 Audit
| ID | Requirement | Pri |
|---|---|---|
| FR-60 | Every agent message, tool call, decision, approval, and deployment is logged immutably | P0 |

## 7. Non-Functional Requirements

| Area | Requirement |
|---|---|
| **Safety** | No unrestricted shell, filesystem, DB, or production access for any LLM; tool gateway with allowlist and scoped credentials |
| **Security** | Logs, repo content, and tickets are untrusted data (prompt-injection defence); secrets redacted; RBAC on approvals |
| **Reliability** | Bounded retries, timeouts, and escalation on every workflow; no infinite loops |
| **State integrity** | Incident lifecycle transitions enforced in the backend |
| **Performance** | Detection-to-incident under 60 s; dashboard updates under 2 s (targets to be validated) |
| **Observability** | AgentZero itself emits metrics/logs/traces |
| **Cost** | Token and cost per incident tracked; model routing by task |
| **Reproducibility** | All failure scenarios scripted and re-runnable |
| **Portability** | Runs with a single `docker compose up` |

## 8. Incident Lifecycle

`DETECTED → INVESTIGATING → ROOT_CAUSE_IDENTIFIED → REPAIR_PROPOSED → VALIDATING → AWAITING_APPROVAL → DEPLOYING → VERIFYING → RESOLVED`

Terminal alternatives: `FAILED`, `REJECTED`, `ROLLED_BACK`, `ESCALATED`.

## 9. Recovery Levels

| Level | Description | Release |
|---|---|---|
| 1 | Automatic operational recovery (predefined, policy-bound safe actions) | R2 |
| 2 | AI-generated repair with human approval | R1/R2 |
| 3 | Pre-approved low-risk autonomous deploys with rollback | R3 (extension) |

## 10. Failure Scenarios (Acceptance Basis)

1. CPU saturation
2. Database performance degradation (inefficient query)
3. Memory leak
4. API failure (HTTP 500)
5. Container crash
6. Vulnerable dependency
7. **Compound/cascading** (slow query → request backlog → memory growth → timeouts)
8. **Negative case:** generated fix fails testing and the system refuses to deploy it

## 11. Success Metrics

| Metric | Definition |
|---|---|
| Detection precision / recall | Genuine alerts / total alerts; detected / actual failures |
| Root cause accuracy | Correct top-1 cause vs injected ground truth |
| MTTD / MTTR | Mean time to detect / restore |
| Repair success rate | Patches passing validation **and** resolving the issue |
| Regression rate | Repairs introducing new failures |
| Rollback success rate | Required rollbacks completed |
| Communication overhead | Extra latency and calls from coordination |
| Token use / cost per incident | LLM consumption and cost |

Baselines: **A** threshold monitoring, **B** single LLM agent, **C** sequential multi-agent, **D** dynamic multi-agent with validation. Same scenarios, same tool and evidence access.

## 12. Research Questions

1. Does multi-agent collaboration improve root-cause accuracy over a single agent?
2. Does dynamic delegation reduce unnecessary LLM calls?
3. Does evidence sharing improve repair reliability?
4. Does an independent Testing Agent reduce failed deployments?
5. Does historical incident retrieval improve diagnosis?
6. How do agent count, accuracy, latency, and cost relate?
7. How well does the system identify cascading failures?

## 13. Acceptance Criteria

**R1 done when:**
- Demo app runs and exposes `/metrics`.
- At least 3 scripted failures are auto-detected and create incidents.
- Diagnostic + Root Cause agents output schema-valid reports with evidence.
- Repair Agent produces a Git patch; Testing Agent validates it in a sandbox.
- A human can approve or reject from the dashboard.

**R2 done when:**
- All 6 single-failure scenarios plus 1 compound scenario work end to end.
- Security Agent blocks at least one vulnerable patch in a test.
- A forced bad deployment is rolled back automatically.
- Audit trail reconstructs any incident fully.

**R3 done when:**
- Configurations A–D are benchmarked with metrics above and results documented.

## 14. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| LLM hallucinated root cause | Wrong fix | Evidence requirements, independent validation, disconfirming-evidence field |
| Prompt injection via logs | Agent hijack | Untrusted-data handling, no instruction-following from evidence, orchestrator-enforced permissions |
| Scope too large | Missed deadline | Three-release plan; build agents in priority order |
| Unsafe code execution | System damage | Docker sandbox, resource limits, allowlist tools |
| Agent loops / cost blowup | Budget | Max retries, timeouts, token budgets per incident |
| Self-reported confidence unreliable | Bad routing | Validate against evidence completeness; treat scores as uncalibrated |
| Multi-agent no better than single-agent | Weak research result | Report honestly; analyse when orchestration helps |

## 15. Open Decisions

| # | Decision | Options | Default |
|---|---|---|---|
| 1 | Implementation level | MVP / Complete advanced / Research-level | Complete advanced + research comparison |
| 2 | First monitored app | E-commerce / Banking / Social / Microservice SaaS / Custom failure-test app | E-commerce |
| 3 | Team size | Solo / 2 / 3 / 4 / 5+ | To confirm |
| 4 | LLM provider | Provider-agnostic | Single common model initially |

## 16. Assumptions

- Metric values, confidence scores, and dashboard numbers in the blueprint are illustrative, not measured.
- The 14-week plan assumes 2–4 people; a solo build needs longer.
- Docker Compose is sufficient for the demo.
