package com.aecp.sdk.events;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.time.Instant;

/** Emitted after every governed agent action completes (success or failure). */
public class ExecutionEvent extends BaseEvent {

    @JsonProperty("agent_id")
    private final String agentId;

    @JsonProperty("execution_id")
    private final String executionId;

    @JsonProperty("timestamp_start")
    private final Instant timestampStart;

    @JsonProperty("timestamp_end")
    private Instant timestampEnd;

    @JsonProperty("action")
    private final String action;

    @JsonProperty("status")
    private String status;

    @JsonProperty("latency_ms")
    private Long latencyMs;

    @JsonProperty("error_message")
    private String errorMessage;

    public ExecutionEvent(String agentId, String executionId, Instant timestampStart, String action) {
        super("agent.execution");
        this.agentId = agentId;
        this.executionId = executionId;
        this.timestampStart = timestampStart;
        this.action = action;
        this.status = "success";
    }

    public String getAgentId() { return agentId; }
    public String getExecutionId() { return executionId; }
    public Instant getTimestampStart() { return timestampStart; }
    public Instant getTimestampEnd() { return timestampEnd; }
    public String getAction() { return action; }
    public String getStatus() { return status; }
    public Long getLatencyMs() { return latencyMs; }
    public String getErrorMessage() { return errorMessage; }

    public void setTimestampEnd(Instant timestampEnd) { this.timestampEnd = timestampEnd; }
    public void setStatus(String status) { this.status = status; }
    public void setLatencyMs(Long latencyMs) { this.latencyMs = latencyMs; }
    public void setErrorMessage(String errorMessage) { this.errorMessage = errorMessage; }
}
