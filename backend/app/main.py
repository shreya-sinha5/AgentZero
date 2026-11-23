"""AgentZero Platform API Main Application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router as api_router

app = FastAPI(
    title="AgentZero Autonomous SRE Platform",
    description="Autonomous multi-agent platform for monitoring, root cause analysis, self-healing, and controlled recovery.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "ok", "service": "agentzero-backend"}
