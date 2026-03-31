package com.example;

import com.aecp.sdk.AecpAgent;
import com.aecp.sdk.AgentConfig;
import com.aecp.sdk.AgentContext;
import com.aecp.sdk.credential.MockCredentialProvider;
import com.aecp.sdk.credential.Token;
import com.aecp.sdk.events.ApiUsageEvent;
import com.aecp.sdk.events.BaseEvent;
import com.aecp.sdk.policy.Policy;
import com.aecp.sdk.policy.PolicyEnforcer;
import com.aecp.sdk.policy.PolicyViolationException;
import com.aecp.sdk.publisher.EventPublisher;
import com.aecp.sdk.publisher.InMemoryEventPublisher;
import com.aecp.sdk.publisher.KafkaEventPublisher;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;

import java.util.List;

/**
 * AECP Example: Java Jira Agent
 * ===============================
 * Demonstrates the full AECP SDK lifecycle:
 *   1. Agent configuration and registration
 *   2. Policy-governed action execution via AecpAgent.executeAction()
 *   3. Manual API usage event emission (equivalent to @track_api_usage in Python)
 *   4. Policy violation detection and SecurityEvent emission
 *   5. Structured JSON event output
 *
 * Run (after installing the SDK locally):
 *   cd sdk/java && mvn install -DskipTests
 *   cd examples/java/jira-agent && mvn compile exec:java
 */
public class JiraAgent {

    // ── Simulated data types ─────────────────────────────────────────────────

    record JiraTicket(String id, String summary, String status) {}

    record LlmResponse(String content, int totalTokens) {}

    // ── Simulated external services ──────────────────────────────────────────

    private static JiraTicket callJiraApi(String summary) throws InterruptedException {
        Thread.sleep(50); // simulate 50ms network latency
        return new JiraTicket("DEMO-42", summary, "Open");
    }

    private static LlmResponse callOpenAi(String prompt) throws InterruptedException {
        Thread.sleep(100); // simulate 100ms LLM latency
        return new LlmResponse(
                "AI-generated description for: " + prompt.substring(0, Math.min(40, prompt.length())),
                420 // simulated total_tokens
        );
    }

    // ── Policy definition ─────────────────────────────────────────────────────

    private static final String POLICY_YAML = """
            agent_id: jira-agent
            allowed_actions:
              - jira.create_ticket
              - jira.search_issues
            credentials:
              type: service_account_only
            cost_limits:
              daily_usd: 50.0
            rate_limits:
              requests_per_minute: 100
            """;

    // ── Main ─────────────────────────────────────────────────────────────────

    public static void main(String[] args) throws Exception {
        sep();
        System.out.println("AECP Java Example Agent");
        sep();

        // ── Step 1: Build infrastructure ──────────────────────────────────────
        String publisherType = System.getenv().getOrDefault("AECP_PUBLISHER_TYPE", "inmemory");
        String bootstrapServers = System.getenv().getOrDefault("AECP_KAFKA_BOOTSTRAP_SERVERS", "localhost:9092");
        EventPublisher publisher;
        if ("kafka".equalsIgnoreCase(publisherType)) {
            System.out.printf("[setup] Using KafkaEventPublisher → %s%n", bootstrapServers);
            publisher = new KafkaEventPublisher(bootstrapServers);
        } else {
            System.out.println("[setup] Using InMemoryEventPublisher (set AECP_PUBLISHER_TYPE=kafka to publish to Kafka)");
            publisher = new InMemoryEventPublisher();
        }
        MockCredentialProvider credentials = new MockCredentialProvider();
        Policy policy = Policy.fromYamlString(POLICY_YAML);
        PolicyEnforcer enforcer = new PolicyEnforcer(policy);

        AgentConfig config = AgentConfig
                .builder("jira-agent", "1.0.0", "platform-team")
                .capabilities(List.of("jira.create_ticket", "jira.search_issues"))
                .controlPlaneUrl("http://localhost:8080")
                .build();

        AecpAgent agent = new AecpAgent(config, publisher, credentials, enforcer);

        // ── Step 2: Register ───────────────────────────────────────────────────
        System.out.println("\n[1] Registering agent with control plane...");
        agent.register();

        // ── Step 3: Execute a permitted action ─────────────────────────────────
        System.out.println("\n[2] Creating Jira ticket (permitted action)...");
        JiraTicket ticket = agent.executeAction("jira.create_ticket", () -> {
            // Obtain credential via provider — never inject a raw token
            Token token = credentials.getServiceToken("jira");
            enforcer.enforceCredential(token);
            return callJiraApi("Fix login page timeout issue");
        });
        System.out.printf("    Created: %s — %s%n", ticket.id(), ticket.summary());

        // ── Step 4: Action + manual API usage tracking ─────────────────────────
        System.out.println("\n[3] Creating ticket with AI enrichment + usage tracking...");
        agent.executeAction("jira.create_ticket", () -> {
            Token token = credentials.getServiceToken("jira");
            enforcer.enforceCredential(token);

            // Call LLM to generate a description
            LlmResponse llm = callOpenAi("Add dark mode support to the dashboard");

            // Emit ApiUsageEvent — equivalent to @track_api_usage in Python SDK
            String execId = AgentContext.current().executionId();
            String corrId  = AgentContext.current().correlationId();
            double costUsd = (llm.totalTokens() / 1000.0) * 0.002;

            ApiUsageEvent usageEvent = new ApiUsageEvent(
                    config.getAgentId(), execId, "openai", llm.totalTokens(), costUsd);
            usageEvent.setCorrelationId(corrId);
            publisher.publish(usageEvent);

            return callJiraApi("Add dark mode: " + llm.content());
        });

        // ── Step 5: Attempt a policy-violating action ──────────────────────────
        System.out.println("\n[4] Attempting unauthorized action (jira.delete_project)...");
        try {
            agent.executeAction("jira.delete_project", () -> "deleted");
        } catch (PolicyViolationException e) {
            System.out.printf("    Blocked as expected: [%s / %s] %s%n",
                    e.getViolationType(), e.getSeverity(), e.getMessage());
        }

        // ── Step 6: Emit heartbeat ─────────────────────────────────────────────
        System.out.println("\n[5] Emitting heartbeat...");
        agent.heartbeat();

        // ── Step 7: Print captured events (in-memory mode only) ────────────────
        if (publisher instanceof InMemoryEventPublisher inMemory) {
            List<BaseEvent> events = inMemory.getEvents();
            ObjectMapper mapper = new ObjectMapper()
                    .registerModule(new JavaTimeModule())
                    .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS)
                    .enable(SerializationFeature.INDENT_OUTPUT);

            System.out.printf("%n");
            sep();
            System.out.printf("Captured %d events:%n", events.size());
            sep();

            for (BaseEvent event : events) {
                System.out.printf("%n[%s]%n", event.getEventType());
                System.out.println(mapper.writeValueAsString(mapper.readTree(event.toJson())));
            }
        } else {
            System.out.printf("%n");
            sep();
            System.out.println("Events published to Kafka topic: aecp.events");
            System.out.println("Observe with:");
            System.out.println("  docker exec -it aecp-kafka kafka-console-consumer \\");
            System.out.println("    --bootstrap-server kafka:29092 \\");
            System.out.println("    --topic aecp.events --from-beginning --property print.key=true");
            sep();
        }

        // ── Shutdown ───────────────────────────────────────────────────────────
        agent.shutdown();
        System.out.printf("%n");
        sep();
        System.out.println("Agent shutdown complete.");
    }

    private static void sep() {
        System.out.println("=".repeat(70));
    }
}
