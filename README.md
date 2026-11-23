# AgentZero

Autonomous multi-agent platform for software monitoring, root cause analysis, self-healing, and controlled recovery.

## Architecture & Layout
```
├── backend/app/          # Core AgentZero platform (FastAPI, State Machine, Tool Gateway, Agents)
├── monitored_app/        # Monitored e-commerce service with Prometheus telemetry
├── infrastructure/       # Docker Compose, Prometheus scraping configs
├── scripts/              # Failure simulation scripts & system verifier
├── tests/                # Unit and integration test suite
└── Documents/            # Project documentation & design specs
    ├── PRD.md            # Product Requirements Document
    ├── Architecture.md   # Architecture specification
    ├── Phases.md         # Development phases and milestones
    ├── Rules.md          # Safety and development rules
    ├── Skills.md         # Agent skills catalogue
    ├── AGENTS.md         # Agent instructions & behavioral mode
    └── Memory.md         # Decision logs and runtime memory design
```

## Quick Start

### 1. Verify Complete System
```bash
python scripts/verify_system.py
```

### 2. Run Tests
```bash
python -m pytest -v tests/
```

### 3. Run Monitored App
```bash
python -m uvicorn monitored_app.app.main:app --port 8001
```

### 4. Run AgentZero Backend
```bash
python -m uvicorn backend.app.main:app --port 8000
```

### 5. Trigger Failure Simulations
```bash
python scripts/simulate_high_latency.py
python scripts/simulate_db_failure.py
python scripts/simulate_memory_leak.py
python scripts/simulate_api_failure.py
```
