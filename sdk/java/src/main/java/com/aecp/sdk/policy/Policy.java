package com.aecp.sdk.policy;

import org.yaml.snakeyaml.Yaml;

import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

/**
 * Agent policy loaded from YAML.
 * Defines what an agent is allowed to do, what credentials it may use,
 * and what cost/rate limits apply.
 */
public class Policy {

    private String agentId;
    private List<String> allowedActions = List.of();
    private String credentialsType = "service_account_only";
    private double dailyCostLimitUsd = 100.0;
    private int requestsPerMinute = 1000;

    /** Load policy from a YAML file on the filesystem. */
    public static Policy fromYaml(Path path) throws Exception {
        try (InputStream is = Files.newInputStream(path)) {
            return fromInputStream(is);
        }
    }

    /** Load policy from a classpath resource. */
    public static Policy fromClasspath(String resourcePath) throws Exception {
        try (InputStream is = Policy.class.getResourceAsStream(resourcePath)) {
            if (is == null) {
                throw new IllegalArgumentException("Policy resource not found: " + resourcePath);
            }
            return fromInputStream(is);
        }
    }

    @SuppressWarnings("unchecked")
    private static Policy fromInputStream(InputStream is) {
        Map<String, Object> data = new Yaml().load(is);
        Policy policy = new Policy();
        policy.agentId = (String) data.get("agent_id");

        if (data.containsKey("allowed_actions")) {
            policy.allowedActions = (List<String>) data.get("allowed_actions");
        }

        if (data.containsKey("credentials")) {
            Map<String, Object> creds = (Map<String, Object>) data.get("credentials");
            if (creds.containsKey("type")) {
                policy.credentialsType = (String) creds.get("type");
            }
        }

        if (data.containsKey("cost_limits")) {
            Map<String, Object> costs = (Map<String, Object>) data.get("cost_limits");
            if (costs.containsKey("daily_usd")) {
                policy.dailyCostLimitUsd = ((Number) costs.get("daily_usd")).doubleValue();
            }
        }

        if (data.containsKey("rate_limits")) {
            Map<String, Object> rates = (Map<String, Object>) data.get("rate_limits");
            if (rates.containsKey("requests_per_minute")) {
                policy.requestsPerMinute = ((Number) rates.get("requests_per_minute")).intValue();
            }
        }

        return policy;
    }

    /** Load policy from a YAML string (e.g. fetched from Control Plane as text). */
    public static Policy fromYamlString(String yaml) throws Exception {
        try (InputStream is = new java.io.ByteArrayInputStream(yaml.getBytes(java.nio.charset.StandardCharsets.UTF_8))) {
            return fromInputStream(is);
        }
    }

    /** Factory for a fully open policy. ONLY appropriate for dev/testing. */
    public static Policy permissive(String agentId) {
        Policy p = new Policy();
        p.agentId = agentId;
        p.allowedActions = List.of("*");
        return p;
    }

    public String getAgentId() { return agentId; }
    public List<String> getAllowedActions() { return allowedActions; }
    public String getCredentialsType() { return credentialsType; }
    public double getDailyCostLimitUsd() { return dailyCostLimitUsd; }
    public int getRequestsPerMinute() { return requestsPerMinute; }
}
