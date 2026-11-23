# AgentZero

Autonomous multi-agent platform for software monitoring, root cause analysis, self-healing, and controlled recovery.

## Architecture & Layout
```
├── backend/app/          # Core AgentZero platform (FastAPI, State Machine, Tool Gateway, Agents)
├── monitored-app/        # Monitored e-commerce service with Prometheus telemetry
├── infrastructure/       # Docker Compose, Prometheus scraping configs
├── scripts/              # Failure simulation scripts (latency, memory, DB, 500s)
├── tests/                # Unit and integration test suite
├── docs/                 # Design, architecture, and workflow docs
├── PRD.md                # Product Requirements Document
├── Architecture.md       # Architecture specification
├── Phases.md             # Development phases and milestones
├── Rules.md              # Safety and development rules
├── Skills.md             # Agent skills catalogue
└── Memory.md             # Decision logs and runtime memory design
```

## Quick Start

### 1. Run Monitored App
```bash
python -m uvicorn monitored_app.app.main:app --port 8001
```

### 2. Run AgentZero Backend
```bash
python -m uvicorn backend.app.main:app --port 8000
```

### 3. Run Tests
```bash
pytest tests/
```

### 4. Trigger Failure Simulations
```bash
python scripts/simulate_high_latency.py
```
