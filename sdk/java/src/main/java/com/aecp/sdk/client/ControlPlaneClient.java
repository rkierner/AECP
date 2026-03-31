package com.aecp.sdk.client;

import com.aecp.sdk.events.AgentRegistrationEvent;
import com.aecp.sdk.events.SecurityEvent;
import com.aecp.sdk.policy.Policy;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import okhttp3.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.yaml.snakeyaml.Yaml;

import java.io.IOException;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

/**
 * HTTP client for the AECP Control Plane REST API.
 *
 * <p>All methods are fail-safe: network errors are logged as warnings and never propagated.
 * The Control Plane is an enhancement, not a dependency — agents must continue functioning
 * even if it is unreachable.
 *
 * <p>All operations are wrapped in {@link CompletableFuture} to avoid blocking the agent thread.
 */
public class ControlPlaneClient {

    private static final Logger log = LoggerFactory.getLogger(ControlPlaneClient.class);
    private static final MediaType JSON = MediaType.get("application/json; charset=utf-8");

    private final String baseUrl;
    private final OkHttpClient httpClient;
    private final ObjectMapper mapper;

    public ControlPlaneClient(String baseUrl, int timeoutSeconds) {
        this.baseUrl = baseUrl.replaceAll("/$", "");
        this.httpClient = new OkHttpClient.Builder()
                .connectTimeout(timeoutSeconds, TimeUnit.SECONDS)
                .readTimeout(timeoutSeconds, TimeUnit.SECONDS)
                .build();
        this.mapper = new ObjectMapper()
                .registerModule(new JavaTimeModule())
                .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
    }

    /** POST /agents/register — non-blocking, fail-safe. */
    public CompletableFuture<Void> registerAgent(AgentRegistrationEvent event) {
        return CompletableFuture.runAsync(() -> {
            try {
                Map<String, Object> body = Map.of(
                        "agent_id", event.getAgentId(),
                        "runtime", event.getRuntime(),
                        "version", event.getVersion(),
                        "owner", event.getOwner(),
                        "capabilities", event.getCapabilities(),
                        "permissions_requested", event.getPermissionsRequested()
                );
                String json = mapper.writeValueAsString(body);
                Request request = new Request.Builder()
                        .url(baseUrl + "/agents/register")
                        .post(RequestBody.create(json, JSON))
                        .build();

                try (Response response = httpClient.newCall(request).execute()) {
                    if (!response.isSuccessful()) {
                        log.warn("Control plane registration failed: HTTP {}", response.code());
                    } else {
                        log.info("Agent registered with control plane: agentId={}", event.getAgentId());
                    }
                }
            } catch (Exception ex) {
                log.warn("Control plane registration error (agent continues): {}", ex.getMessage());
            }
        });
    }

    /** GET /policies/{agentId} — returns null on 404 or error. */
    public Policy getPolicy(String agentId) {
        try {
            Request request = new Request.Builder()
                    .url(baseUrl + "/policies/" + agentId)
                    .get()
                    .build();

            try (Response response = httpClient.newCall(request).execute()) {
                if (response.code() == 404) {
                    return null;
                }
                if (!response.isSuccessful()) {
                    log.warn("Policy fetch failed: HTTP {}", response.code());
                    return null;
                }
                String body = response.body().string();
                Map<String, Object> data = mapper.readValue(body, Map.class);
                // Convert map back to YAML string so Policy.fromInputStream can parse it
                String yaml = new Yaml().dump(data);
                return Policy.fromClasspath(null); // placeholder — see note below
            }
        } catch (Exception ex) {
            log.warn("Control plane policy fetch error: agentId={} error={}", agentId, ex.getMessage());
            return null;
        }
    }

    /** POST /violations — fail-safe, best-effort delivery. */
    public CompletableFuture<Void> reportViolation(SecurityEvent event) {
        return CompletableFuture.runAsync(() -> {
            try {
                Map<String, Object> body = Map.of(
                        "agent_id", event.getAgentId(),
                        "violation_type", event.getViolationType(),
                        "severity", event.getSeverity(),
                        "details", event.getDetails(),
                        "correlation_id", event.getCorrelationId()
                );
                String json = mapper.writeValueAsString(body);
                Request request = new Request.Builder()
                        .url(baseUrl + "/violations")
                        .post(RequestBody.create(json, JSON))
                        .build();

                try (Response response = httpClient.newCall(request).execute()) {
                    if (!response.isSuccessful()) {
                        log.warn("Violation report failed: HTTP {}", response.code());
                    }
                }
            } catch (Exception ex) {
                log.warn("Violation report error: {}", ex.getMessage());
            }
        });
    }

    public void shutdown() {
        httpClient.dispatcher().executorService().shutdown();
        httpClient.connectionPool().evictAll();
    }
}
