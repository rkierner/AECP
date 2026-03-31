from __future__ import annotations

import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Generator


@dataclass
class _ExecutionContext:
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""


# ContextVar is the correct primitive for asyncio-safe ambient context.
# threading.local would NOT work correctly across async coroutines.
_context_var: ContextVar[_ExecutionContext] = ContextVar(
    "_aecp_context",
    default=_ExecutionContext(),
)


class AgentContext:
    """
    Ambient context carrier for correlation and execution IDs.

    Uses contextvars.ContextVar for safe propagation across asyncio coroutines.
    The new_execution() context manager creates an isolated execution scope
    and restores the parent context on exit — safe for nested calls.

    Example:
        with AgentContext.new_execution() as ctx:
            print(ctx.execution_id)   # unique per action
            print(ctx.correlation_id) # shared across the request chain
    """

    @staticmethod
    def current() -> _ExecutionContext:
        return _context_var.get()

    @staticmethod
    def set_agent_id(agent_id: str) -> None:
        ctx = _context_var.get()
        _context_var.set(
            _ExecutionContext(
                correlation_id=ctx.correlation_id,
                execution_id=ctx.execution_id,
                agent_id=agent_id,
            )
        )

    @staticmethod
    @contextmanager
    def new_execution(
        correlation_id: str | None = None,
    ) -> Generator[_ExecutionContext, None, None]:
        """
        Context manager that creates a new execution scope.
        Preserves the parent correlation_id unless overridden.
        Restores the parent context on exit.
        """
        parent = _context_var.get()
        new_ctx = _ExecutionContext(
            correlation_id=correlation_id or parent.correlation_id,
            execution_id=str(uuid.uuid4()),
            agent_id=parent.agent_id,
        )
        token = _context_var.set(new_ctx)
        try:
            yield new_ctx
        finally:
            _context_var.reset(token)
