"""Tests for EventPublisher implementations."""

import threading

import pytest

from aecp.publisher.in_memory_publisher import InMemoryEventPublisher
from aecp.events.registration import AgentRegistrationEvent
from aecp.events.execution import ExecutionEvent
from aecp.events.base import StatusType

from datetime import datetime, timezone


@pytest.fixture
def publisher():
    return InMemoryEventPublisher()


@pytest.fixture
def reg_event():
    return AgentRegistrationEvent(
        agent_id="test-agent",
        runtime="python",
        version="1.0.0",
        owner="test-team",
    )


@pytest.fixture
def exec_event():
    now = datetime.now(tz=timezone.utc)
    return ExecutionEvent(
        agent_id="test-agent",
        execution_id="exec-123",
        timestamp_start=now,
        timestamp_end=now,
        action="jira.create_ticket",
        status=StatusType.SUCCESS,
        latency_ms=50,
    )


class TestInMemoryPublisher:
    def test_publish_single(self, publisher, reg_event):
        publisher.publish(reg_event)
        events = publisher.get_events()
        assert len(events) == 1
        assert events[0].event_id == reg_event.event_id

    def test_publish_batch(self, publisher, reg_event, exec_event):
        publisher.publish_batch([reg_event, exec_event])
        assert len(publisher.get_events()) == 2

    def test_get_events_returns_snapshot(self, publisher, reg_event):
        publisher.publish(reg_event)
        snapshot = publisher.get_events()
        publisher.clear()
        # Snapshot is independent of the store
        assert len(snapshot) == 1
        assert len(publisher.get_events()) == 0

    def test_filter_by_type(self, publisher, reg_event, exec_event):
        publisher.publish(reg_event)
        publisher.publish(exec_event)
        executions = publisher.get_events_by_type("agent.execution")
        assert len(executions) == 1
        assert executions[0].action == "jira.create_ticket"  # type: ignore

    def test_thread_safety(self, publisher, reg_event):
        """Concurrent publishes must not lose events or raise."""
        errors = []

        def publish_many():
            try:
                for _ in range(50):
                    publisher.publish(reg_event)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=publish_many) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
        assert len(publisher.get_events()) == 200

    def test_shutdown_is_safe(self, publisher):
        publisher.shutdown()  # must not raise
