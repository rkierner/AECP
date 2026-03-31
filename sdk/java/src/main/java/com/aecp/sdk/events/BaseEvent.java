package com.aecp.sdk.events;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;

import java.time.Instant;
import java.util.UUID;

/**
 * Root event model. All AECP events extend this.
 * Matches base-event.schema.json in common/schema/.
 */
public abstract class BaseEvent {

    private static final ObjectMapper MAPPER = new ObjectMapper()
            .registerModule(new JavaTimeModule())
            .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);

    @JsonProperty("event_id")
    private final String eventId;

    @JsonProperty("event_type")
    private final String eventType;

    @JsonProperty("schema_version")
    private final String schemaVersion;

    @JsonProperty("timestamp")
    private final Instant timestamp;

    @JsonProperty("correlation_id")
    private String correlationId;

    protected BaseEvent(String eventType) {
        this.eventId = UUID.randomUUID().toString();
        this.eventType = eventType;
        this.schemaVersion = "1.0";
        this.timestamp = Instant.now();
        this.correlationId = UUID.randomUUID().toString();
    }

    public String getEventId() { return eventId; }
    public String getEventType() { return eventType; }
    public String getSchemaVersion() { return schemaVersion; }
    public Instant getTimestamp() { return timestamp; }
    public String getCorrelationId() { return correlationId; }

    public void setCorrelationId(String correlationId) {
        this.correlationId = correlationId;
    }

    public String toJson() {
        try {
            return MAPPER.writeValueAsString(this);
        } catch (Exception e) {
            // Must not throw — return a minimal fallback
            return "{\"event_id\":\"" + eventId + "\",\"event_type\":\"" + eventType
                    + "\",\"error\":\"serialization_failed\"}";
        }
    }
}
