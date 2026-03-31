package com.aecp.sdk;

import com.aecp.sdk.client.ControlPlaneClient;
import com.aecp.sdk.credential.CredentialProvider;
import com.aecp.sdk.events.*;
import com.aecp.sdk.policy.PolicyEnforcer;
import com.aecp.sdk.policy.PolicyViolationException;
import com.aecp.sdk.publisher.EventPublisher;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Instant;
import java.util.Map;
import java.util.concurrent.Callable;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

/**
 * Main entry point for AECP-instrumented Java agents.
 *
 * <p>Responsibilities:
 * <ul>
 *   <li>Register agent identity with the Control Plane
 *   <li>Emit all AECP event types via the configured {@link EventPublisher}
 *   <li>Enforce policy before every action
 *   <li>Schedule periodic heartbeats
 * </ul>
 *
 * <p>Example:
 * <pre>{@code
 * AgentConfig config = AgentConfig.builder("jira-agent", "1.0.0", "platform-team")
 *     .capabilities(List.of("jira.create_ticket"))
 *     .build();
 *
 * AecpAgent agent = new AecpAgent(config,
 *     new InMemoryEventPublisher(),
 *     new MockCredentialProvider(),
 *     new PolicyEnforcer(Policy.permissive("jira-agent")));
 *
 * agent.register();
 *
 * String result = agent.executeAction("jira.create_ticket", () -> {
 *     // ... actual work ...
 *     return "JIRA-123";
 * });
 * }</pre>
 */
public class AecpAgent {

    private static final Logger log = LoggerFactory.getLogger(AecpAgent.class);

    private final AgentConfig config;
    private final EventPublisher publisher;
    private final CredentialProvider credentialProvider;
    private final PolicyEnforcer policyEnforcer;
    private final ControlPlaneClient controlPlaneClient;
    private final ScheduledExecutorService scheduler;
    private final Instant startTime;

    public AecpAgent(
            AgentConfig config,
            EventPublisher publisher,
            CredentialProvider credentialProvider,
            PolicyEnforcer policyEnforcer) {
        this.config = config;
        this.publisher = publisher;
        this.credentialProvider = credentialProvider;
        this.policyEnforcer = policyEnforcer;
        this.controlPlaneClient = new ControlPlaneClient(
                config.getControlPlaneUrl(),
                config.getControlPlaneTimeoutSeconds()
        );
        this.scheduler = Executors.newSingleThreadScheduledExecutor(r -> {
            Thread t = new Thread(r, "aecp-scheduler-" + config.getAgentId());
            t.setDaemon(true);
            return t;
        });
        this.startTime = Instant.now();
        AgentContext.setAgentId(config.getAgentId());
    }

    /**
     * Register this agent with the Control Plane and emit a registration event to MQ.
     * Safe to call multiple times (idempotent on the Control Plane side).
     */
    public void register() {
        AgentRegistrationEvent event = new AgentRegistrationEvent(
                config.getAgentId(),
                config.getRuntime(),
                config.getVersion(),
                config.getOwner(),
                config.getCapabilities(),
                config.getPermissionsRequested()
        );
        event.setCorrelationId(AgentContext.current().correlationId());

        // Control Plane registration is best-effort — agent proceeds regardless
        controlPlaneClient.registerAgent(event);

        // MQ event is always emitted
        safePublish(event);
        log.info("Agent registered: agentId={} runtime={} version={}",
                config.getAgentId(), config.getRuntime(), config.getVersion());
    }

    /**
     * Execute an action with full AECP instrumentation.
     *
     * <ul>
     *   <li>Enforces action policy — throws {@link PolicyViolationException} if denied
     *   <li>Creates an execution scope with a fresh execution_id
     *   <li>Emits {@link ExecutionEvent} after completion (success or failure)
     *   <li>Publisher failures are caught and logged — never re-thrown
     * </ul>
     *
     * @param action  Dot-notation action name (e.g. "jira.create_ticket")
     * @param work    The actual work to execute
     * @param <T>     Return type of the work
     * @return        Result of the work
     * @throws PolicyViolationException if the action is not permitted by policy
     * @throws RuntimeException wrapping any exception thrown by work
     */
    public <T> T executeAction(String action, Callable<T> work) {
        try (AgentContext.ExecutionScope scope = AgentContext.newExecution()) {
            AgentContext.Context ctx = scope.context();

            // Policy check — emits SecurityEvent and re-throws on violation
            try {
                policyEnforcer.enforceAction(action);
            } catch (PolicyViolationException e) {
                safePublish(new SecurityEvent(
                        config.getAgentId(),
                        e.getViolationType(),
                        e.getSeverity(),
                        Map.of("message", e.getMessage(), "blocked", true, "action_attempted", action)
                ));
                throw e;
            }

            Instant start = Instant.now();
            ExecutionEvent execEvent = new ExecutionEvent(
                    config.getAgentId(), ctx.executionId(), start, action);
            execEvent.setCorrelationId(ctx.correlationId());

            try {
                T result = work.call();
                Instant end = Instant.now();
                execEvent.setTimestampEnd(end);
                execEvent.setLatencyMs(end.toEpochMilli() - start.toEpochMilli());
                execEvent.setStatus("success");
                return result;
            } catch (PolicyViolationException e) {
                throw e;
            } catch (Exception e) {
                Instant end = Instant.now();
                execEvent.setTimestampEnd(end);
                execEvent.setLatencyMs(end.toEpochMilli() - start.toEpochMilli());
                execEvent.setStatus("failure");
                execEvent.setErrorMessage(e.getMessage());
                throw new RuntimeException("Action '" + action + "' failed: " + e.getMessage(), e);
            } finally {
                // Always emit — even on exception
                CompletableFuture.runAsync(() -> safePublish(execEvent));
            }
        }
    }

    /** Emit a single heartbeat event. */
    public void heartbeat() {
        long uptimeSeconds = Instant.now().getEpochSecond() - startTime.getEpochSecond();
        HeartbeatEvent event = new HeartbeatEvent(
                config.getAgentId(),
                "healthy",
                Instant.now(),
                Map.of("uptime_seconds", uptimeSeconds)
        );
        event.setCorrelationId(AgentContext.current().correlationId());
        safePublish(event);
    }

    /** Start the background heartbeat scheduler. Stops on shutdown(). */
    public void startHeartbeat() {
        scheduler.scheduleAtFixedRate(
                this::heartbeat,
                config.getHeartbeatIntervalSeconds(),
                config.getHeartbeatIntervalSeconds(),
                TimeUnit.SECONDS
        );
        log.debug("Heartbeat scheduled every {}s", config.getHeartbeatIntervalSeconds());
    }

    /** Flush publisher, stop scheduler, and release HTTP client resources. */
    public void shutdown() {
        scheduler.shutdown();
        try {
            scheduler.awaitTermination(5, TimeUnit.SECONDS);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        publisher.shutdown();
        controlPlaneClient.shutdown();
        log.info("AecpAgent shutdown complete: agentId={}", config.getAgentId());
    }

    /** Expose publisher for use in interceptors etc. */
    public EventPublisher getPublisher() { return publisher; }
    public AgentConfig getConfig() { return config; }

    private void safePublish(BaseEvent event) {
        try {
            publisher.publish(event);
        } catch (Exception ex) {
            log.warn("Publisher error suppressed: {}", ex.getMessage());
        }
    }
}
