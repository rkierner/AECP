from __future__ import annotations

import structlog
from fastapi import APIRouter, HTTPException, Request, status

from ..models import AgentMetadata, AgentRegistrationRequest, AgentRegistrationResponse

router = APIRouter()
logger = structlog.get_logger()


@router.get(
    "",
    response_model=list[AgentMetadata],
    summary="List all registered agents",
)
async def list_agents(request: Request) -> list[AgentMetadata]:
    return request.app.state.agent_store.list_all()


@router.post(
    "/register",
    response_model=AgentRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register an agent",
    description="Idempotent — re-registering an existing agent_id updates its metadata.",
)
async def register_agent(request: Request, body: AgentRegistrationRequest) -> AgentRegistrationResponse:
    store = request.app.state.agent_store
    metadata = await store.register(body)
    logger.info(
        "agent_registered",
        agent_id=body.agent_id,
        runtime=body.runtime,
        version=body.version,
        owner=body.owner,
    )
    return AgentRegistrationResponse(
        agent_id=metadata.agent_id,
        registered_at=metadata.registered_at,
    )


@router.get(
    "/{agent_id}",
    response_model=AgentMetadata,
    summary="Get agent metadata",
)
async def get_agent(request: Request, agent_id: str) -> AgentMetadata:
    store = request.app.state.agent_store
    metadata = await store.get(agent_id)
    if not metadata:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    return metadata
