from __future__ import annotations

import structlog
from fastapi import APIRouter, Request, status

from ..models import ViolationReport

router = APIRouter()
logger = structlog.get_logger()

# In-memory violation log.
# Production upgrade: forward directly to the MQ (Kafka) using the same
# EventPublisher interface the SDKs use, so violations appear in aecp.events.
_violation_log: list[ViolationReport] = []


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Report a security violation",
    description="Accepts violation reports from SDK agents. Stored in-memory and logged as structured events.",
)
async def report_violation(request: Request, report: ViolationReport) -> dict:
    _violation_log.append(report)
    logger.warning(
        "security_violation_reported",
        agent_id=report.agent_id,
        violation_type=report.violation_type,
        severity=report.severity,
        correlation_id=report.correlation_id,
        blocked=report.details.get("blocked"),
    )
    return {"status": "accepted", "correlation_id": report.correlation_id}


@router.get(
    "",
    summary="List all reported violations",
    response_model=list[ViolationReport],
)
async def list_violations() -> list[ViolationReport]:
    return _violation_log
