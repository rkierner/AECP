from __future__ import annotations

import time

import structlog

from .base import EventPublisher
from ..events.base import BaseEvent

logger = structlog.get_logger()

# Exponential backoff delays in seconds for retry attempts
_RETRY_DELAYS_S = [0.1, 0.2, 0.4]


def _require_confluent_kafka():
    try:
        from confluent_kafka import Producer, KafkaException  # noqa: F401
        return Producer
    except ImportError as exc:
        raise RuntimeError(
            "confluent-kafka is required for KafkaEventPublisher. "
            "Install it with: pip install 'aecp-sdk[kafka]'"
        ) from exc


class KafkaEventPublisher(EventPublisher):
    """
    Kafka-backed event publisher.

    Design:
    - Partitioned by agent_id for per-agent ordering guarantees
    - Retry with exponential backoff (max 3 attempts)
    - Final failures routed to dead-letter topic (dlq_topic)
    - Publish errors are always caught — they never crash the agent

    Configuration via constructor args or environment variables:
      AECP_KAFKA_BOOTSTRAP_SERVERS
      AECP_KAFKA_TOPIC
      AECP_KAFKA_DLQ_TOPIC
    """

    def __init__(
        self,
        bootstrap_servers: str,
        topic: str = "aecp.events",
        dlq_topic: str = "aecp.events.dlq",
    ) -> None:
        Producer = _require_confluent_kafka()
        self._topic = topic
        self._dlq_topic = dlq_topic
        self._producer = Producer(
            {
                "bootstrap.servers": bootstrap_servers,
                "client.id": "aecp-sdk-python",
                "acks": "all",
                "retries": 0,       # Manual retry logic below
                "linger.ms": 5,     # Micro-batching for throughput
                "batch.size": 16384,
            }
        )

    def publish(self, event: BaseEvent) -> None:
        self._deliver_with_retry(event)

    def publish_batch(self, events: list[BaseEvent]) -> None:
        for event in events:
            self._deliver_with_retry(event)
        self._producer.flush(timeout=5)

    def _deliver_with_retry(self, event: BaseEvent) -> None:
        payload = event.to_json().encode("utf-8")
        # Use agent_id as partition key for ordering per agent
        key = getattr(event, "agent_id", event.event_id).encode("utf-8")

        for attempt, delay in enumerate(_RETRY_DELAYS_S, start=1):
            try:
                self._producer.produce(
                    topic=self._topic,
                    key=key,
                    value=payload,
                    on_delivery=self._log_delivery,
                )
                self._producer.poll(0)
                return
            except Exception as exc:
                logger.warning(
                    "kafka_publish_attempt_failed",
                    attempt=attempt,
                    max_attempts=len(_RETRY_DELAYS_S),
                    error=str(exc),
                    event_id=event.event_id,
                )
                if attempt < len(_RETRY_DELAYS_S):
                    time.sleep(delay)

        # All retries exhausted — route to DLQ
        self._send_to_dlq(event, payload)

    def _send_to_dlq(self, event: BaseEvent, payload: bytes) -> None:
        try:
            self._producer.produce(topic=self._dlq_topic, value=payload)
            self._producer.poll(0)
            logger.error(
                "event_routed_to_dlq",
                event_id=event.event_id,
                event_type=event.event_type,
                dlq_topic=self._dlq_topic,
            )
        except Exception as exc:
            # DLQ itself failed — log and move on; observability must not crash agents
            logger.error(
                "dlq_publish_failed",
                event_id=event.event_id,
                error=str(exc),
            )

    @staticmethod
    def _log_delivery(err, msg) -> None:
        if err:
            logger.error(
                "kafka_delivery_failed",
                error=str(err),
                topic=msg.topic() if msg else "unknown",
            )

    def shutdown(self) -> None:
        self._producer.flush(timeout=10)
        logger.info("kafka_publisher_shutdown")
