from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, Request

router = APIRouter()
logger = structlog.get_logger()


@router.get(
    "/{agent_id}",
    summary="Get policy for an agent",
    description="Returns the full policy document. 404 if no policy is defined for this agent.",
)
async def get_policy(request: Request, agent_id: str) -> dict[str, Any]:
    loader = request.app.state.policy_loader
    policy = loader.get_policy(agent_id)
    if policy is None:
        raise HTTPException(
            status_code=404,
            detail=f"No policy defined for agent '{agent_id}'. "
                   f"Create a YAML file in the policies/ directory.",
        )
    return policy
