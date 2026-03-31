from __future__ import annotations

import asyncio
import json
import logging

import structlog

from .event_store import EventStore

logger = structlog.get_logger()


async def start_kafka_consumer(event_store: EventStore, bootstrap_servers: str) -> None:
    """
    Background asyncio task that consumes from aecp.events and ingests into EventStore.

    Uses asyncio.to_thread so the synchronous confluent-kafka Consumer doesn't block
    the event loop. Silently handles missing confluent-kafka (import error logged once).
    """
    try:
        from confluent_kafka import Consumer, KafkaError, KafkaException
    except ImportError:
        logger.warning(
            "kafka_consumer_disabled",
            reason="confluent-kafka not installed; install it to enable live event ingestion",
        )
        return

    # Capture the running loop before entering the thread
    loop = asyncio.get_running_loop()

    def _consume_loop() -> None:
        consumer = Consumer(
            {
                "bootstrap.servers": bootstrap_servers,
                "group.id": "aecp-control-plane-dashboard",
                "auto.offset.reset": "latest",
                "enable.auto.commit": True,
            }
        )
        consumer.subscribe(["aecp.events"])
        logger.info("kafka_consumer_subscribed", topic="aecp.events")

        try:
            while True:
                msg = consumer.poll(timeout=1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    logger.error("kafka_consumer_error", error=str(msg.error()))
                    continue

                try:
                    event = json.loads(msg.value().decode("utf-8"))
                    # Schedule ingestion on the event loop from this thread
                    asyncio.run_coroutine_threadsafe(
                        event_store.ingest(event),
                        loop,
                    )
                except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                    logger.warning("kafka_message_decode_error", error=str(exc))
        except KafkaException as exc:
            logger.error("kafka_consumer_fatal", error=str(exc))
        finally:
            consumer.close()

    # Run the blocking consumer loop in a thread pool
    await asyncio.to_thread(_consume_loop)
