from __future__ import annotations

import threading
from datetime import datetime, timezone

import structlog

from .config import AgentConfig
from .context import AgentContext
from .events.registration import AgentRegistrationEvent
from .events.heartbeat import HeartbeatEvent
from .events.base import AgentStatusType
from .publisher.base import EventPublisher
from .credential.base import CredentialProvider
from .policy.enforcer import PolicyEnforcer
from .client import ControlPlaneClient
from . import decorators as _registry

logger = structlog.get_logger()


class AecpAgent:
    """
    Main entry point for AECP-instrumented agents.

    Responsibilities:
    - Register agent identity with the Control Plane
    - Populate the decorator registry so @agent_action and @track_api_usage work
    - Emit heartbeats on a background thread
    - Provide an explicit execute() method as an alternative to decorators

    Usage:
        config = AgentConfig(agent_id="my-agent", version="1.0.0", owner="my-team")
        publisher = InMemoryEventPublisher()
        agent = AecpAgent(config, publisher, MockCredentialProvider(), enforcer)
        agent.register()

        # Option A: decorators (applied at module level)
        @agent_action("my.action")
        def do_work(): ...

        # Option B: explicit execution
        result = agent.execute("my.action", do_work, arg1, arg2)
    """

    def __init__(
        self,
        config: AgentConfig,
        publisher: EventPublisher,
        credential_provider: CredentialProvider,
        policy_enforcer: PolicyEnforcer,
    ) -> None:
        self.config = config
        self.publisher = publisher
        self.credential_provider = credential_provider
        self.policy_enforcer = policy_enforcer
        self._client = ControlPlaneClient(
            config.control_plane_url,
            config.control_plane_timeout_seconds,
        )
        self._heartbeat_thread: threading.Thread | None = None
        self._shutdown_event = threading.Event()
        self._start_time = datetime.now(tz=timezone.utc)

        # Register in the module-level decorator registries
        _registry._publisher_registry[config.agent_id] = publisher
        _registry._enforcer_registry[config.agent_id] = policy_enforcer
        AgentContext.set_agent_id(config.agent_id)

    def register(self) -> None:
        """
        Register this agent with the Control Plane and emit a registration event to MQ.
        Safe to call multiple times (idempotent on the Control Plane side).
        """
        ctx = AgentContext.current()
        event = AgentRegistrationEvent(
            agent_id=self.config.agent_id,
            runtime=self.config.runtime,
            version=self.config.version,
            owner=self.config.owner,
            capabilities=self.config.capabilities,
            permissions_requested=self.config.permissions_requested,
            correlation_id=ctx.correlation_id,
        )

        # Control Plane registration is best-effort — agent proceeds regardless
        self._client.register_agent(event)

        # MQ event is always emitted
        self._safe_publish(event)

        logger.info(
            "agent_registered",
            agent_id=self.config.agent_id,
            runtime=self.config.runtime,
            version=self.config.version,
        )

    def heartbeat(self) -> None:
        """Emit a heartbeat event. Called automatically by start_heartbeat()."""
        now = datetime.now(tz=timezone.utc)
        uptime = int((now - self._start_time).total_seconds())
        event = HeartbeatEvent(
            agent_id=self.config.agent_id,
            status=AgentStatusType.HEALTHY,
            last_seen=now,
            metadata={"uptime_seconds": uptime},
            correlation_id=AgentContext.current().correlation_id,
        )
        self._safe_publish(event)

    def start_heartbeat(self) -> None:
        """Start the background heartbeat thread. Stops when shutdown() is called."""

        def _loop() -> None:
            while not self._shutdown_event.wait(self.config.heartbeat_interval_seconds):
                self.heartbeat()

        self._heartbeat_thread = threading.Thread(
            target=_loop,
            daemon=True,
            name=f"aecp-heartbeat-{self.config.agent_id}",
        )
        self._heartbeat_thread.start()
        logger.debug("heartbeat_started", interval_seconds=self.config.heartbeat_interval_seconds)

    def execute(self, action: str, func: callable, *args, **kwargs):
        """
        Explicit alternative to the @agent_action decorator.
        Enforces policy, records execution, and emits ExecutionEvent.

        Raises PolicyViolationError if the action is not permitted.
        Re-raises any exception from func after recording the failure.
        """
        from .decorators import agent_action

        wrapped = agent_action(action, agent_id=self.config.agent_id)(func)
        return wrapped(*args, **kwargs)

    def shutdown(self) -> None:
        """Flush the publisher, stop the heartbeat thread, and clean up."""
        self._shutdown_event.set()
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=5)
        self.publisher.shutdown()
        logger.info("agent_shutdown", agent_id=self.config.agent_id)

    def _safe_publish(self, event) -> None:
        try:
            self.publisher.publish(event)
        except Exception as exc:
            logger.warning("publisher_error_suppressed", error=str(exc))
