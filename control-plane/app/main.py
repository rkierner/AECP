from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .event_store import EventStore
from .policy_loader import PolicyLoader
from .store import AgentStore
from .routers import agents, policies, violations, events

# Configure structlog for JSON output — downstream consumers (New Relic, Datadog)
# can parse these directly without a log parsing pipeline.
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()

# Singletons — created once, shared across requests via app.state
_agent_store = AgentStore()
_policy_loader = PolicyLoader(Path(__file__).parent.parent / "policies")
_event_store = EventStore()


@asynccontextmanager
async def lifespan(app: FastAPI):
    _policy_loader.load()
    logger.info(
        "control_plane_started",
        policies_loaded=len(_policy_loader.policies),
        policy_agents=list(_policy_loader.policies.keys()),
    )

    # Start Kafka consumer if bootstrap servers are configured
    kafka_task = None
    bootstrap_servers = os.getenv("AECP_KAFKA_BOOTSTRAP_SERVERS")
    if bootstrap_servers:
        from .kafka_consumer import start_kafka_consumer
        import asyncio
        kafka_task = asyncio.create_task(
            start_kafka_consumer(_event_store, bootstrap_servers)
        )
        logger.info("kafka_consumer_started", bootstrap_servers=bootstrap_servers)

    yield

    if kafka_task:
        kafka_task.cancel()
        try:
            await kafka_task
        except Exception:
            pass
    logger.info("control_plane_shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title="AECP Control Plane",
        version="1.0.0",
        description=(
            "Agent Execution Control Plane — registers agents, serves policies, "
            "and accepts security violation reports."
        ),
        lifespan=lifespan,
    )

    # CORS — allow dashboard origin; default "*" for local dev
    cors_origins = os.getenv("AECP_CORS_ORIGINS", "*").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    # Inject singletons so routers can access them via request.app.state
    app.state.agent_store = _agent_store
    app.state.policy_loader = _policy_loader
    app.state.event_store = _event_store

    app.include_router(agents.router, prefix="/agents", tags=["agents"])
    app.include_router(policies.router, prefix="/policies", tags=["policies"])
    app.include_router(violations.router, prefix="/violations", tags=["violations"])
    app.include_router(events.router, prefix="/events", tags=["events"])

    @app.get("/health", tags=["ops"], summary="Health check")
    async def health():
        return {
            "status": "ok",
            "agents_registered": len(_agent_store.list_all()),
            "policies_loaded": len(_policy_loader.policies),
        }

    return app


app = create_app()
