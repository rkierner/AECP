package com.aecp.sdk.events;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.Map;

/**
 * Emitted when a policy violation is detected.
 * Always emitted before execution is blocked — never suppressed.
 */
public class SecurityEvent extends BaseEvent {

    @JsonProperty("agent_id")
    private final String agentId;

    @JsonProperty("violation_type")
    private final String violationType;

    @JsonProperty("severity")
    private final String severity;

    @JsonProperty("details")
    private final Map<String, Object> details;

    public SecurityEvent(
            String agentId,
            String violationType,
            String severity,
            Map<String, Object> details) {
        super("agent.security");
        this.agentId = agentId;
        this.violationType = violationType;
        this.severity = severity;
        this.details = details;
    }

    public String getAgentId() { return agentId; }
    public String getViolationType() { return violationType; }
    public String getSeverity() { return severity; }
    public Map<String, Object> getDetails() { return details; }
}
