package com.aecp.sdk.events;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.time.Instant;
import java.util.Map;

/** Emitted periodically (default 30s) to signal liveness. */
public class HeartbeatEvent extends BaseEvent {

    @JsonProperty("agent_id")
    private final String agentId;

    @JsonProperty("status")
    private final String status;

    @JsonProperty("last_seen")
    private final Instant lastSeen;

    @JsonProperty("metadata")
    private final Map<String, Object> metadata;

    public HeartbeatEvent(String agentId, String status, Instant lastSeen, Map<String, Object> metadata) {
        super("agent.heartbeat");
        this.agentId = agentId;
        this.status = status;
        this.lastSeen = lastSeen;
        this.metadata = metadata;
    }

    public String getAgentId() { return agentId; }
    public String getStatus() { return status; }
    public Instant getLastSeen() { return lastSeen; }
    public Map<String, Object> getMetadata() { return metadata; }
}
