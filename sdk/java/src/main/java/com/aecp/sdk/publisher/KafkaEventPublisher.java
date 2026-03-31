package com.aecp.sdk.publisher;

import com.aecp.sdk.events.BaseEvent;
import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.apache.kafka.common.serialization.StringSerializer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Duration;
import java.util.List;
import java.util.Properties;
import java.util.concurrent.TimeUnit;

/**
 * Kafka-backed event publisher.
 *
 * <p>Design decisions:
 * <ul>
 *   <li>Partitioned by agent_id for per-agent ordering guarantees
 *   <li>Retry with exponential backoff — max 3 attempts (100ms, 200ms, 400ms)
 *   <li>Final failures routed to DLQ topic (aecp.events.dlq)
 *   <li>All exceptions caught — never propagated to caller
 * </ul>
 *
 * <p>Requires: kafka-clients on the classpath (declared optional in pom.xml).
 */
public class KafkaEventPublisher implements EventPublisher {

    private static final Logger log = LoggerFactory.getLogger(KafkaEventPublisher.class);

    private static final long[] RETRY_DELAYS_MS = {100L, 200L, 400L};

    private final KafkaProducer<String, String> producer;
    private final String topic;
    private final String dlqTopic;

    public KafkaEventPublisher(String bootstrapServers) {
        this(bootstrapServers, "aecp.events", "aecp.events.dlq");
    }

    public KafkaEventPublisher(String bootstrapServers, String topic, String dlqTopic) {
        this.topic = topic;
        this.dlqTopic = dlqTopic;
        this.producer = new KafkaProducer<>(buildProducerConfig(bootstrapServers));
    }

    private static Properties buildProducerConfig(String bootstrapServers) {
        Properties props = new Properties();
        props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
        props.put(ProducerConfig.CLIENT_ID_CONFIG, "aecp-sdk-java");
        props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());
        props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, StringSerializer.class.getName());
        props.put(ProducerConfig.ACKS_CONFIG, "all");
        props.put(ProducerConfig.RETRIES_CONFIG, 0);        // manual retry below
        props.put(ProducerConfig.LINGER_MS_CONFIG, 5);      // micro-batching
        props.put(ProducerConfig.BATCH_SIZE_CONFIG, 16384);
        return props;
    }

    @Override
    public void publish(BaseEvent event) {
        deliverWithRetry(event);
    }

    @Override
    public void publishBatch(List<BaseEvent> events) {
        for (BaseEvent event : events) {
            deliverWithRetry(event);
        }
        try {
            producer.flush();
        } catch (Exception e) {
            log.error("Flush failed after batch publish", e);
        }
    }

    private void deliverWithRetry(BaseEvent event) {
        String payload = event.toJson();
        // Partition key = agent_id for ordering; fall back to event_id
        String key = extractAgentId(event);

        for (int attempt = 0; attempt < RETRY_DELAYS_MS.length; attempt++) {
            try {
                ProducerRecord<String, String> record = new ProducerRecord<>(topic, key, payload);
                producer.send(record, (metadata, ex) -> {
                    if (ex != null) {
                        log.error("Kafka delivery callback error: topic={} offset={}", topic, ex.getMessage());
                    }
                });
                return; // success
            } catch (Exception ex) {
                log.warn("Kafka publish attempt {} failed: {}", attempt + 1, ex.getMessage());
                if (attempt < RETRY_DELAYS_MS.length - 1) {
                    sleepQuietly(RETRY_DELAYS_MS[attempt]);
                }
            }
        }

        // All retries exhausted — route to DLQ
        sendToDlq(event, payload);
    }

    private void sendToDlq(BaseEvent event, String payload) {
        try {
            producer.send(new ProducerRecord<>(dlqTopic, event.getEventId(), payload));
            log.error("Event routed to DLQ: eventId={} eventType={} dlqTopic={}",
                    event.getEventId(), event.getEventType(), dlqTopic);
        } catch (Exception ex) {
            // DLQ itself failed — log and move on; must not crash the agent
            log.error("DLQ publish failed: eventId={} error={}", event.getEventId(), ex.getMessage());
        }
    }

    private String extractAgentId(BaseEvent event) {
        try {
            var method = event.getClass().getMethod("getAgentId");
            return (String) method.invoke(event);
        } catch (Exception e) {
            return event.getEventId();
        }
    }

    private static void sleepQuietly(long millis) {
        try {
            TimeUnit.MILLISECONDS.sleep(millis);
        } catch (InterruptedException ie) {
            Thread.currentThread().interrupt();
        }
    }

    @Override
    public void shutdown() {
        try {
            producer.flush();
            producer.close(Duration.ofSeconds(10));
            log.info("KafkaEventPublisher shutdown complete");
        } catch (Exception e) {
            log.error("Error during KafkaEventPublisher shutdown", e);
        }
    }
}
