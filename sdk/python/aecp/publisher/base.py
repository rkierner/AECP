from __future__ import annotations

from abc import ABC, abstractmethod

from ..events.base import BaseEvent


class EventPublisher(ABC):
    """
    Abstract base for all AECP event publishers.

    CONTRACT: All implementations MUST be fail-safe.
    Exceptions must be caught internally and never propagated to agent code.
    Observability infrastructure must never break agent functionality.
    """

    @abstractmethod
    def publish(self, event: BaseEvent) -> None:
        """Publish a single event. Must not raise exceptions."""
        ...

    @abstractmethod
    def publish_batch(self, events: list[BaseEvent]) -> None:
        """Publish multiple events. Must not raise exceptions."""
        ...

    @abstractmethod
    def shutdown(self) -> None:
        """Flush pending events and release resources cleanly."""
        ...
