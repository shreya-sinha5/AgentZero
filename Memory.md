# AgentZero — Memory

This file has two parts:
1. **System memory design:** how AgentZero stores and retrieves incident knowledge at runtime.
2. **Project memory:** a living log of decisions, assumptions, and context for the team and AI coding assistants.

---

# Part 1 — System Memory Design

## 1. Memory Types

| Type | Scope | Lifetime | Storage | Owner |
|---|---|---|---|---|
| **Working memory** | One incident run | Until incident closes | LangGraph `IncidentState` + checkpoints | Orchestrator |
| **Episodic memory** | Past incidents | Permanent | PostgreSQL + pgvector | Learning Agent |
| **Semantic/knowledge memory** | Distilled patterns and recurring root causes | Permanent, reviewed | PostgreSQL | Learning Agent |
| **Procedural memory** | Approved runbooks and Level 1 recovery policies | Versioned | Git (policy files) | Humans |
| **Audit memory** | Every action and decision | Append-only, permanent | PostgreSQL | Platform |

LLMs are **not** fine-tuned or self-trained. Memory is controlled retrieval and analysis.

## 2. Working Memory (per incident)

The shared `IncidentState` holds logs, metrics, traces, reports, patch, test and security results, approval, deployment status, retry counters, budget, and execution history. Agents read what they need and append their outputs, so nobody rebuilds the investigation from scratch. Checkpoints allow resume after a crash.

## 3. Episodic Memory: Incident Records

Stored when an incident reaches a terminal state.

```json
{
  "incident_id": "INC-1042",
  "service": "payment-api",
  "symptoms": ["latency spike", "timeouts"],
  "root_cause": "full table scan from new query",
  "causal_chain": ["deploy v1.4", "expensive query", "DB load", "timeouts"],
  "evidence_refs": ["loki:...", "trace:...", "metric:..."],
  "fix": {"branch": "agentzero/inc-1042-1", "diff_ref": "...", "summary": "..."},
  "tests": {"verdict": "pass", "perf_delta": "..."},
  "security": {"verdict": "pass"},
  "approval": {"approver": "...", "decision": "approved"},
  "deployment": {"version": "...", "status": "success", "rolled_back": false},
  "outcome": "RESOLVED",
  "mttd_s": 0, "mttr_s": 0, "tokens": 0, "cost": 0.0,
  "embedding": "<vector>",
  "created_at": "..."
}
```
Numbers above are placeholders.

**Write rules**
- Write on terminal state only (`RESOLVED`, `ROLLED_BACK`, `REJECTED`, `FAILED`, `ESCALATED`).
- Store **failed** repairs and why they failed, not just successes.
- Store references to telemetry, not raw logs.
- Redact secrets before embedding or storing.
- Mark records `verified` only after a human or successful post-deploy verification confirms the root cause.

## 4. Retrieval

1. Build a query from current symptoms, service, and top hypotheses.
2. Vector search (pgvector) filtered by service and failure type; hybrid with keyword match on error signatures.
3. Return top-k (default 5) with similarity, outcome, and `verified` flag.
4. Root Cause Agent treats results as **hints with evidence requirements**, never as conclusions.
5. Repair Agent may reuse a past fix only as a starting point; it still passes full validation.

**Poisoning defence:** retrieved records are untrusted data like logs. Unverified or failed records are labelled and weighted down. Records cannot contain executable instructions that agents follow.

## 5. Semantic Memory: Pattern Mining

Learning Agent periodically (or on incident close):
- Detects recurring root causes (e.g. connection-pool exhaustion seen 3 times).
- Proposes preventive monitoring or alert rules (as suggestions for human review).
- Generates post-incident reports.

Suggestions never change live policies automatically.

## 6. Procedural Memory

Runbooks and Level 1 recovery policies live in version-controlled files. Agents read them; only humans change them via PR.

## 7. Retention and Privacy

| Data | Retention |
|---|---|
| Incident records and audit | Permanent for the project; configurable |
| Raw logs and metrics | Governed by Loki/Prometheus retention |
| Embeddings | Regenerated if the embedding model changes |
| Secrets | Never stored; redacted at ingestion |

## 8. Memory Evaluation

Measure memory's value in the benchmark (research question 5): root-cause accuracy and MTTR with memory enabled vs disabled, on recurring and novel failures. Also track retrieval precision@k and harmful-retrieval rate (a wrong hint misleading an agent).

## 9. Suggested Tables

`incident_knowledge(id, incident_id, summary, root_cause, fix_ref, outcome, verified, embedding, created_at)`
`pattern_insights(id, pattern, incident_ids, suggestion, status, created_at)`
`agent_executions`, `agent_messages` (audit, see `architecture.md`)

---

# Part 2 — Project Memory (living log)

> Update after any architectural decision, scope change, or lesson learned. AI coding assistants: read this before large changes.

## Project Snapshot
- **Project:** AgentZero, autonomous multi-agent software monitoring, root cause analysis, self-healing and controlled recovery
- **Category:** Advanced AI + Multi-Agent Systems
- **Stack:** Python, FastAPI, LangGraph, Pydantic, React + TypeScript + Tailwind, PostgreSQL + pgvector, Redis, Prometheus, Grafana, Loki, OpenTelemetry, Docker, GitHub Actions
- **Current phase:** Phase 0 (decisions and setup)
- **Core differentiator:** evidence-driven multi-agent repair loop with independent validation and measurable outcomes

## Decisions Log

| Date | Decision | Rationale | Status |
|---|---|---|---|
| 2026-11-23 | Platform is application-independent, demonstrated on own e-commerce app | Avoids a one-app debugging tool | Approved |
| 2026-11-23 | Docker Compose first; Kubernetes is an extension | Sufficient for demo, less overhead | Approved |
| 2026-11-23 | Production deploys require human approval in v1 | Safety | Approved |
| 2026-11-23 | Repair outputs Git diffs on temp branches only | Reviewable, safe | Approved |
| 2026-11-23 | Deterministic anomaly detection; LLM for interpretation | Reliability | Approved |
| 2026-11-23 | Memory = retrieval, not model training | Control and safety | Approved |
| 2026-11-24 | Target repo locked to https://github.com/shreya-sinha5/AgentZero.git | User selection | Approved |

## Open Questions

| # | Question | Options | Owner | Resolved? |
|---|---|---|---|---|
| 1 | Implementation level | MVP / Complete advanced / Research | Team | Resolved: R1 MVP |
| 2 | First monitored app | E-commerce (default) / other | Team | Resolved: E-commerce |
| 3 | Team size | Solo–5+ | Team | Resolved: Solo |
| 4 | LLM provider | Provider-agnostic | Team | Resolved: Provider-agnostic |

## Assumptions
- Blueprint figures (metrics, confidence, dashboard counts, chart values) are illustrative, not measured.
- 14-week plan assumes 2–4 people.
- Evaluation will compare configurations A (threshold), B (single LLM), C (sequential MAS), D (dynamic MAS).

## Lessons Learned
_(empty: add entries as phases complete)_

| Date | Phase | Lesson | Action taken |
|---|---|---|---|

## Phase Progress

| Phase | Status | Notes |
|---|---|---|
| 0 Decisions and setup | In progress | |
| 1 Foundation | Not started | |
| 2 Incident detection | Not started | |
| 3 Orchestration | Not started | |
| 4 Repair | Not started | |
| 5 Security and deployment | Not started | |
| 6 Frontend and integration | Not started | |
| 7 Evaluation | Not started | |

## Document Map

| File | Purpose |
|---|---|
| `PRD.md` | What and why: requirements, scope, metrics |
| `architecture.md` | How: components, workflow, data, APIs, threats |
| `phases.md` | When: phased plan and exit criteria |
| `rules.md` | Safety, development, and evaluation rules |
| `Skills.md` | Agent capabilities, tools, developer skills |
| `memory.md` | System memory design and project decision log |
