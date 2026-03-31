from __future__ import annotations

import asyncio
import functools
from datetime import datetime, timezone
from typing import Any, Callable, TypeVar

import structlog

from .context import AgentContext
from .events.execution import ExecutionEvent
from .events.api_usage import ApiUsageEvent
from .events.security import SecurityEvent
from .events.base import StatusType
from .policy.enforcer import PolicyViolationError

logger = structlog.get_logger()

F = TypeVar("F", bound=Callable[..., Any])

# Per-agent registries populated by AecpAgent.__init__().
# Decorators look up publisher and enforcer at call time (not decoration time),
# so they work regardless of definition order.
_publisher_registry: dict[str, Any] = {}
_enforcer_registry: dict[str, Any] = {}


def _safe_publish(publisher: Any, event: Any) -> None:
    """Publish without propagating exceptions. Observability must never crash agents."""
    if publisher is None:
        return
    try:
        publisher.publish(event)
    except Exception as exc:
        logger.warning(
            "publisher_error_suppressed",
            error=str(exc),
            event_type=getattr(event, "event_type", "unknown"),
        )


def agent_action(action_name: str, agent_id: str | None = None):
    """
    Decorator that instruments a function as a governed agent action.

    Behavior:
    - Enforces action policy before execution (raises PolicyViolationError if denied)
    - Emits ExecutionEvent after execution (success or failure)
    - On policy violation: emits SecurityEvent then re-raises PolicyViolationError
    - Publisher failures are caught and logged — never re-raised
    - Works with both sync and async functions

    Usage:
        @agent_action("jira.create_ticket")
        def create_ticket(summary: str) -> dict:
            ...

        @agent_action("jira.create_ticket")
        async def create_ticket_async(summary: str) -> dict:
            ...
    """

    def decorator(func: F) -> F:

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            _aid = agent_id or AgentContext.current().agent_id
            publisher = _publisher_registry.get(_aid)
            enforcer = _enforcer_registry.get(_aid)

            with AgentContext.new_execution() as ctx:
                timestamp_start = datetime.now(tz=timezone.utc)
                status = StatusType.SUCCESS
                error_message = None

                if enforcer:
                    try:
                        enforcer.enforce_action(action_name)
                    except PolicyViolationError as e:
                        _safe_publish(
                            publisher,
                            SecurityEvent(
                                agent_id=_aid,
                                violation_type=e.violation_type,
                                severity=e.severity,
                                details={
                                    "message": str(e),
                                    "blocked": True,
                                    "action_attempted": action_name,
                                },
                                correlation_id=ctx.correlation_id,
                            ),
                        )
                        raise

                try:
                    return await func(*args, **kwargs)
                except PolicyViolationError:
                    raise
                except Exception as exc:
                    status = StatusType.FAILURE
                    error_message = str(exc)
                    raise
                finally:
                    timestamp_end = datetime.now(tz=timezone.utc)
                    latency_ms = int(
                        (timestamp_end - timestamp_start).total_seconds() * 1000
                    )
                    _safe_publish(
                        publisher,
                        ExecutionEvent(
                            agent_id=_aid,
                            execution_id=ctx.execution_id,
                            timestamp_start=timestamp_start,
                            timestamp_end=timestamp_end,
                            action=action_name,
                            status=status,
                            latency_ms=latency_ms,
                            error_message=error_message,
                            correlation_id=ctx.correlation_id,
                        ),
                    )

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            _aid = agent_id or AgentContext.current().agent_id
            publisher = _publisher_registry.get(_aid)
            enforcer = _enforcer_registry.get(_aid)

            with AgentContext.new_execution() as ctx:
                timestamp_start = datetime.now(tz=timezone.utc)
                status = StatusType.SUCCESS
                error_message = None

                if enforcer:
                    try:
                        enforcer.enforce_action(action_name)
                    except PolicyViolationError as e:
                        _safe_publish(
                            publisher,
                            SecurityEvent(
                                agent_id=_aid,
                                violation_type=e.violation_type,
                                severity=e.severity,
                                details={
                                    "message": str(e),
                                    "blocked": True,
                                    "action_attempted": action_name,
                                },
                                correlation_id=ctx.correlation_id,
                            ),
                        )
                        raise

                try:
                    return func(*args, **kwargs)
                except PolicyViolationError:
                    raise
                except Exception as exc:
                    status = StatusType.FAILURE
                    error_message = str(exc)
                    raise
                finally:
                    timestamp_end = datetime.now(tz=timezone.utc)
                    latency_ms = int(
                        (timestamp_end - timestamp_start).total_seconds() * 1000
                    )
                    _safe_publish(
                        publisher,
                        ExecutionEvent(
                            agent_id=_aid,
                            execution_id=ctx.execution_id,
                            timestamp_start=timestamp_start,
                            timestamp_end=timestamp_end,
                            action=action_name,
                            status=status,
                            latency_ms=latency_ms,
                            error_message=error_message,
                            correlation_id=ctx.correlation_id,
                        ),
                    )

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore

    return decorator


def track_api_usage(
    provider: str,
    cost_per_1k_tokens: float = 0.002,
    agent_id: str | None = None,
):
    """
    Decorator that tracks LLM / external API token usage.

    Token count extraction (tries in order):
    1. result.usage.total_tokens  (OpenAI SDK style)
    2. result.usage.input_tokens + result.usage.output_tokens  (Anthropic SDK style)
    3. result.tokens_used          (custom)
    4. result["tokens_used"]       (dict return)
    5. Falls back to 0 if none found

    Emits ApiUsageEvent after each call. Works with sync and async functions.

    Usage:
        @track_api_usage("openai", cost_per_1k_tokens=0.005)
        def call_llm(prompt: str):
            return openai_client.chat.completions.create(...)
    """

    def decorator(func: F) -> F:

        def _emit_usage(result: Any, _aid: str, publisher: Any, ctx: Any) -> None:
            tokens_used = 0
            try:
                if hasattr(result, "usage"):
                    usage = result.usage
                    if hasattr(usage, "total_tokens"):
                        tokens_used = usage.total_tokens
                    elif hasattr(usage, "input_tokens") and hasattr(usage, "output_tokens"):
                        tokens_used = usage.input_tokens + usage.output_tokens
                elif hasattr(result, "tokens_used"):
                    tokens_used = result.tokens_used
                elif isinstance(result, dict):
                    tokens_used = result.get("tokens_used", 0)
            except Exception:
                pass

            estimated_cost = (tokens_used / 1000.0) * cost_per_1k_tokens
            _safe_publish(
                publisher,
                ApiUsageEvent(
                    agent_id=_aid,
                    execution_id=ctx.execution_id,
                    provider=provider,
                    tokens_used=tokens_used,
                    estimated_cost_usd=estimated_cost,
                    correlation_id=ctx.correlation_id,
                ),
            )

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            _aid = agent_id or AgentContext.current().agent_id
            publisher = _publisher_registry.get(_aid)
            ctx = AgentContext.current()
            result = await func(*args, **kwargs)
            _emit_usage(result, _aid, publisher, ctx)
            return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            _aid = agent_id or AgentContext.current().agent_id
            publisher = _publisher_registry.get(_aid)
            ctx = AgentContext.current()
            result = func(*args, **kwargs)
            _emit_usage(result, _aid, publisher, ctx)
            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore

    return decorator
