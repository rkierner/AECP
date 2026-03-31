package com.aecp.sdk.events;

import com.fasterxml.jackson.annotation.JsonProperty;

/** Emitted after every LLM or external API call to track token consumption and cost. */
public class ApiUsageEvent extends BaseEvent {

    @JsonProperty("agent_id")
    private final String agentId;

    @JsonProperty("execution_id")
    private final String executionId;

    @JsonProperty("provider")
    private final String provider;

    @JsonProperty("token_type")
    private final String tokenType = "service_account";

    @JsonProperty("tokens_used")
    private final int tokensUsed;

    @JsonProperty("estimated_cost_usd")
    private final double estimatedCostUsd;

    @JsonProperty("model")
    private String model;

    public ApiUsageEvent(
            String agentId,
            String executionId,
            String provider,
            int tokensUsed,
            double estimatedCostUsd) {
        super("agent.api_usage");
        this.agentId = agentId;
        this.executionId = executionId;
        this.provider = provider;
        this.tokensUsed = tokensUsed;
        this.estimatedCostUsd = estimatedCostUsd;
    }

    public String getAgentId() { return agentId; }
    public String getExecutionId() { return executionId; }
    public String getProvider() { return provider; }
    public String getTokenType() { return tokenType; }
    public int getTokensUsed() { return tokensUsed; }
    public double getEstimatedCostUsd() { return estimatedCostUsd; }
    public String getModel() { return model; }

    public ApiUsageEvent withModel(String model) {
        this.model = model;
        return this;
    }
}
