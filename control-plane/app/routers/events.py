from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional

import structlog
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from ..models import DashboardStats, EventVolumeBucket

router = APIRouter()
logger = structlog.get_logger()

_DAY_ABBRS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


@router.get(
    "",
    summary="List recent events",
    description="Returns the most recent events from the in-memory store, newest first.",
)
async def list_events(
    request: Request,
    limit: int = 200,
    event_type: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> list[dict]:
    event_store = request.app.state.event_store
    return await event_store.list_recent(limit=limit, event_type=event_type, agent_id=agent_id)


@router.get(
    "/stats",
    response_model=DashboardStats,
    summary="Aggregated dashboard statistics",
    description="Computes live stats from the in-memory event and agent stores.",
)
async def get_stats(request: Request) -> DashboardStats:
    event_store = request.app.state.event_store
    agent_store = request.app.state.agent_store
    policy_loader = request.app.state.policy_loader

    now = datetime.now(tz=timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())

    all_events = event_store.snapshot()

    # --- Active agents (heartbeat within 5 minutes) ---
    heartbeats: dict[str, datetime] = {}
    for e in all_events:
        if e.get("event_type") == "agent.heartbeat":
            agent_id = e.get("agent_id", "")
            ts_str = e.get("timestamp", "")
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if agent_id not in heartbeats or ts > heartbeats[agent_id]:
                    heartbeats[agent_id] = ts
            except (ValueError, AttributeError):
                pass

    active_agents = sum(
        1 for ts in heartbeats.values() if (now - ts).total_seconds() < 300
    )
    # Fall back to registered agent count if no heartbeats yet
    if active_agents == 0:
        active_agents = len(agent_store.list_all())

    # --- Events today ---
    today_events = [
        e for e in all_events
        if _parse_ts(e.get("timestamp")) >= today_start
    ]
    events_today = len(today_events)

    # --- Security violations today ---
    violations_today = sum(
        1 for e in today_events if e.get("event_type") == "agent.security"
    )

    # --- Daily spend today ---
    daily_spend = sum(
        e.get("estimated_cost_usd", 0.0)
        for e in today_events
        if e.get("event_type") == "agent.api_usage"
    )

    # Budget: sum all agent daily_usd limits from policies
    total_budget = 0.0
    for agent in agent_store.list_all():
        policy = policy_loader.get_policy(agent.agent_id)
        if policy:
            total_budget += policy.get("cost_limits", {}).get("daily_usd", 100.0)
    if total_budget == 0.0:
        total_budget = 500.0  # sensible fallback when no policies loaded

    # --- Event volume series (hourly buckets, last 24 hours) ---
    buckets: dict[str, int] = {}
    for i in range(24):
        bucket_hour = (now - timedelta(hours=23 - i)).replace(minute=0, second=0, microsecond=0)
        buckets[bucket_hour.isoformat()] = 0

    for e in all_events:
        if e.get("event_type") not in ("agent.execution", "agent.api_usage"):
            continue
        ts = _parse_ts(e.get("timestamp"))
        if ts < now - timedelta(hours=24):
            continue
        bucket = ts.replace(minute=0, second=0, microsecond=0)
        key = bucket.isoformat()
        if key in buckets:
            buckets[key] += 1

    event_volume_series = [
        EventVolumeBucket(hour=k, count=v) for k, v in sorted(buckets.items())
    ]

    # --- Cost by agent, current week (Mon–Sun) ---
    cost_by_agent: dict[str, dict[str, float]] = defaultdict(lambda: {d: 0.0 for d in _DAY_ABBRS})
    for e in all_events:
        if e.get("event_type") != "agent.api_usage":
            continue
        ts = _parse_ts(e.get("timestamp"))
        if ts < week_start:
            continue
        agent_id = e.get("agent_id", "unknown")
        day_abbr = _DAY_ABBRS[ts.weekday()]
        cost_by_agent[agent_id][day_abbr] += e.get("estimated_cost_usd", 0.0)

    return DashboardStats(
        active_agents=active_agents,
        active_agents_delta="+0",
        events_today=events_today,
        events_today_delta="+0%",
        security_violations=violations_today,
        violations_delta="+0",
        daily_spend_usd=round(daily_spend, 2),
        spend_budget_usd=round(total_budget, 2),
        spend_delta="+0%",
        event_volume_series=event_volume_series,
        cost_by_agent_series={k: dict(v) for k, v in cost_by_agent.items()},
    )


@router.get(
    "/stream",
    summary="Live event stream (SSE)",
    description="Server-Sent Events stream of all events as they are ingested.",
)
async def stream_events(request: Request):
    event_store = request.app.state.event_store
    q = await event_store.subscribe()

    async def event_generator():
        # Replay last 50 events for immediate hydration
        recent = await event_store.list_recent(limit=50)
        for event in reversed(recent):
            yield f"data: {json.dumps(event)}\n\n"

        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(q.get(), timeout=15.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    # Send a keepalive comment to prevent proxy timeouts
                    yield ": keepalive\n\n"
        finally:
            await event_store.unsubscribe(q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


def _parse_ts(ts_str: object) -> datetime:
    """Parse an ISO 8601 timestamp string, returning epoch if unparseable."""
    if not isinstance(ts_str, str):
        return datetime.fromtimestamp(0, tz=timezone.utc)
    try:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except ValueError:
        return datetime.fromtimestamp(0, tz=timezone.utc)
