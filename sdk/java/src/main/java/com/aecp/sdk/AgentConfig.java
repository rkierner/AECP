package com.aecp.sdk;

import java.util.List;

/**
 * Immutable configuration for an AECP-instrumented Java agent.
 * Constructed via {@link Builder}.
 */
public final class AgentConfig {

    private final String agentId;
    private final String version;
    private final String owner;
    private final List<String> capabilities;
    private final List<String> permissionsRequested;
    private final String runtime;
    private final String controlPlaneUrl;
    private final int controlPlaneTimeoutSeconds;
    private final String kafkaBootstrapServers;
    private final String kafkaTopic;
    private final String kafkaDlqTopic;
    private final long heartbeatIntervalSeconds;

    private AgentConfig(Builder b) {
        this.agentId = b.agentId;
        this.version = b.version;
        this.owner = b.owner;
        this.capabilities = List.copyOf(b.capabilities);
        this.permissionsRequested = List.copyOf(b.permissionsRequested);
        this.runtime = b.runtime;
        this.controlPlaneUrl = b.controlPlaneUrl;
        this.controlPlaneTimeoutSeconds = b.controlPlaneTimeoutSeconds;
        this.kafkaBootstrapServers = b.kafkaBootstrapServers;
        this.kafkaTopic = b.kafkaTopic;
        this.kafkaDlqTopic = b.kafkaDlqTopic;
        this.heartbeatIntervalSeconds = b.heartbeatIntervalSeconds;
    }

    public String getAgentId() { return agentId; }
    public String getVersion() { return version; }
    public String getOwner() { return owner; }
    public List<String> getCapabilities() { return capabilities; }
    public List<String> getPermissionsRequested() { return permissionsRequested; }
    public String getRuntime() { return runtime; }
    public String getControlPlaneUrl() { return controlPlaneUrl; }
    public int getControlPlaneTimeoutSeconds() { return controlPlaneTimeoutSeconds; }
    public String getKafkaBootstrapServers() { return kafkaBootstrapServers; }
    public String getKafkaTopic() { return kafkaTopic; }
    public String getKafkaDlqTopic() { return kafkaDlqTopic; }
    public long getHeartbeatIntervalSeconds() { return heartbeatIntervalSeconds; }

    public static Builder builder(String agentId, String version, String owner) {
        return new Builder(agentId, version, owner);
    }

    public static final class Builder {
        private final String agentId;
        private final String version;
        private final String owner;
        private List<String> capabilities = List.of();
        private List<String> permissionsRequested = List.of();
        private String runtime = "java";
        private String controlPlaneUrl = "http://localhost:8080";
        private int controlPlaneTimeoutSeconds = 5;
        private String kafkaBootstrapServers = "localhost:9092";
        private String kafkaTopic = "aecp.events";
        private String kafkaDlqTopic = "aecp.events.dlq";
        private long heartbeatIntervalSeconds = 30L;

        Builder(String agentId, String version, String owner) {
            this.agentId = agentId;
            this.version = version;
            this.owner = owner;
        }

        public Builder capabilities(List<String> capabilities) {
            this.capabilities = capabilities; return this;
        }
        public Builder permissionsRequested(List<String> perms) {
            this.permissionsRequested = perms; return this;
        }
        public Builder controlPlaneUrl(String url) {
            this.controlPlaneUrl = url; return this;
        }
        public Builder kafkaBootstrapServers(String servers) {
            this.kafkaBootstrapServers = servers; return this;
        }
        public Builder kafkaTopic(String topic) {
            this.kafkaTopic = topic; return this;
        }
        public Builder heartbeatIntervalSeconds(long interval) {
            this.heartbeatIntervalSeconds = interval; return this;
        }

        public AgentConfig build() {
            return new AgentConfig(this);
        }
    }
}
