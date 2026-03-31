from __future__ import annotations

import threading

import structlog

from .base import EventPublisher
from ..events.base import BaseEvent

logger = structlog.get_logger()


class InMemoryEventPublisher(EventPublisher):
    """
    Thread-safe in-memory publisher.

    Primary use cases:
    - Unit and integration testing
    - Local development without Kafka
    - CI pipelines

    Use get_events() to inspect what was published in tests.
    """

    def __init__(self) -> None:
        self._events: list[BaseEvent] = []
        self._lock = threading.Lock()

    def publish(self, event: BaseEvent) -> None:
        with self._lock:
            self._events.append(event)
        logger.debug(
            "event_published_inmemory",
            event_type=event.event_type,
            event_id=event.event_id,
        )

    def publish_batch(self, events: list[BaseEvent]) -> None:
        with self._lock:
            self._events.extend(events)
        logger.debug("batch_published_inmemory", count=len(events))

    def shutdown(self) -> None:
        pass  # Nothing to flush for in-memory

    def get_events(self) -> list[BaseEvent]:
        """Return a snapshot of all published events. Thread-safe."""
        with self._lock:
            return list(self._events)

    def get_events_by_type(self, event_type: str) -> list[BaseEvent]:
        """Filter events by event_type string."""
        with self._lock:
            return [e for e in self._events if e.event_type == event_type]

    def clear(self) -> None:
        """Reset the event log. Useful between test cases."""
        with self._lock:
            self._events.clear()
