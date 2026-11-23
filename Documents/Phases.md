# AgentZero — Development Phases

**Version:** 1.0 · **Date:** 2026-11-23
Assumes 14 weeks with 2–4 people; a solo build should stretch timelines. Releases R1/R2/R3 map to phases as shown.

| Phase | Weeks | Release | Deliverable |
|---|---|---|---|
| 0 | Pre-work | — | Decisions locked |
| 1 | 1–2 | R1 | Monitored application |
| 2 | 3–4 | R1 | Automated incident detection |
| 3 | 5–6 | R1/R2 | Collaborative incident investigation |
| 4 | 7–8 | R1/R2 | AI-generated validated patches |
| 5 | 9–10 | R2 | Controlled self-healing |
| 6 | 11–12 | R2 | Complete working platform |
| 7 | 13–14 | R3 | Evaluated project |

---

## Phase 0 — Decisions and Setup
- [x] Choose implementation level (MVP / complete advanced / research-level)
- [x] Choose first monitored app (default: e-commerce)
- [x] Confirm team size and assign module owners
- [x] Choose LLM provider behind a provider-agnostic interface
- [x] Create repo, branching strategy, CI skeleton, `.env.example`

**Exit:** `PRD.md` approved; repo scaffolded per `architecture.md`.

## Phase 1 — Foundation (Weeks 1–2)
- [x] Build demo e-commerce app (auth, catalogue, cart, orders, payment simulation, background worker)
- [x] PostgreSQL + Docker Compose
- [x] Prometheus metrics (`/metrics`), OpenTelemetry instrumentation, Loki logging
- [ ] Grafana baseline dashboard

**Exit:** `docker compose up` runs the app with live metrics, logs, traces.

## Phase 2 — Incident Detection (Weeks 3–4)
- [ ] Metric collection and Alertmanager rules
- [ ] Alert receiver, dedupe, grouping, severity, incident IDs
- [ ] Anomaly detection (thresholds, moving average, Isolation Forest)
- [ ] Incident APIs and lifecycle state machine (backend-enforced)
- [ ] Failure simulation scripts (latency, DB, memory, API, CPU, crash)

**Exit:** each scripted failure creates exactly one grouped incident; 200 alerts ≠ 200 investigations.

## Phase 3 — Multi-Agent Orchestration (Weeks 5–6)
- [ ] LangGraph setup, `IncidentState`, checkpoints, retry/timeout policies
- [ ] Tool gateway skeleton with allowlists and audit logging
- [ ] Diagnostic Agent, Root Cause Agent
- [ ] Database Agent, Infrastructure Agent
- [ ] Conditional routing and disagreement adjudication
- [ ] Prompt-injection defences on evidence ingestion

**Exit:** a DB-latency incident yields a schema-valid root-cause report with evidence and disconfirming checks.

## Phase 4 — Intelligent Repair (Weeks 7–8)
- [ ] Repo tools; Git manager (temp branches)
- [ ] Repair Agent generating diffs with rationale and side effects
- [ ] Docker sandbox runner with resource limits
- [ ] Testing Agent: unit, integration, regression, before/after performance
- [ ] Repair ↔ Testing feedback loop with max retries

**Exit:** the slow-query scenario produces a patch that passes tests in the sandbox; a deliberately bad patch is rejected.

## Phase 5 — Security and Deployment (Weeks 9–10)
- [ ] Security Agent with Bandit, Semgrep, Trivy, dependency scan; veto path
- [ ] Approval service and RBAC
- [ ] Deployment Agent: image build, staging, smoke tests, canary
- [ ] Health verification and automatic rollback
- [ ] Level 1 safe operational recovery policies

**Exit:** forced bad deploy rolls back automatically; vulnerable patch is blocked.

## Phase 6 — Frontend and Integration (Weeks 11–12)
- [ ] Overview, Monitoring, Agent Control Centre
- [ ] Incident investigation, Repair review (diff view), Deployment centre
- [ ] Knowledge base search
- [ ] WebSocket/SSE live updates
- [ ] Incident Learning Agent and pgvector retrieval
- [ ] End-to-end integration tests

**Exit:** full demo flow works from the dashboard without terminal intervention.

## Phase 7 — Evaluation and Documentation (Weeks 13–14)
- [ ] Run all 6 single scenarios + compound cascading scenario + negative case (failed fix refused)
- [ ] Benchmark configurations A (threshold), B (single LLM), C (sequential MAS), D (dynamic MAS)
- [ ] Collect metrics: precision, recall, root-cause accuracy, MTTD, MTTR, repair success, regression rate, rollback success, overhead, tokens, cost
- [ ] Repeat each scenario enough times to report variance
- [ ] Write report, API docs, incident workflow docs; rehearse demo

**Exit:** results answer the research questions in `PRD.md` honestly, including where multi-agent does not help.

---

## Agent Build Order
1. Monitoring → 2. Diagnostic → 3. Root Cause → 4. Repair → 5. Testing → 6. Security → 7. Deployment → 8. Database/Infrastructure specialists → 9. Incident Learning. Build the Orchestrator early and grow it incrementally.

## Demo Script (Final)
1. Healthy baseline (illustrative: 180 ms API, 25 ms DB, 0.2% errors)
2. Inject inefficient query; monitoring detects latency spike
3. Diagnostic → Database → Root Cause link it to the new query
4. Repair proposes optimised query as a Git patch
5. Independent tests and security scan
6. Human reviews and approves
7. Deploy, verify, resolve; Learning Agent stores the incident
8. Second run: bad fix fails testing, deployment refused

## Phase Gates
Each phase ends with: demo of the exit criterion, passing tests, updated docs, and an entry in `memory.md` (decisions log).

## Risk-Driven Cut List (if time is short)
Cut in this order: Kubernetes → multi-agent debate → adaptive agent selection → Level 3 autonomy → Learning Agent extras → Infrastructure Agent depth. Never cut: validation, approval, rollback, audit trail, evaluation.
