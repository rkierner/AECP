package com.aecp.sdk.events;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

/** Emitted once on agent startup. */
public class AgentRegistrationEvent extends BaseEvent {

    @JsonProperty("agent_id")
    private final String agentId;

    @JsonProperty("runtime")
    private final String runtime;

    @JsonProperty("version")
    private final String version;

    @JsonProperty("owner")
    private final String owner;

    @JsonProperty("capabilities")
    private final List<String> capabilities;

    @JsonProperty("permissions_requested")
    private final List<String> permissionsRequested;

    public AgentRegistrationEvent(
            String agentId,
            String runtime,
            String version,
            String owner,
            List<String> capabilities,
            List<String> permissionsRequested) {
        super("agent.registration");
        this.agentId = agentId;
        this.runtime = runtime;
        this.version = version;
        this.owner = owner;
        this.capabilities = capabilities != null ? capabilities : List.of();
        this.permissionsRequested = permissionsRequested != null ? permissionsRequested : List.of();
    }

    public String getAgentId() { return agentId; }
    public String getRuntime() { return runtime; }
    public String getVersion() { return version; }
    public String getOwner() { return owner; }
    public List<String> getCapabilities() { return capabilities; }
    public List<String> getPermissionsRequested() { return permissionsRequested; }
}
