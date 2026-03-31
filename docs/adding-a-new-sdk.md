# Adding a New Runtime SDK

This guide walks through implementing an AECP SDK for a new language runtime (e.g., Node.js, Go, .NET).

## Checklist

A compliant SDK must implement all of the following:

- [ ] All 5 event types (matching `common/schema/`)
- [ ] `EventPublisher` interface (with at least `InMemoryPublisher` and `KafkaPublisher`)
- [ ] `CredentialProvider` interface (with `MockProvider` and a Vault placeholder)
- [ ] `PolicyEnforcer` (action allowlist + credential enforcement)
- [ ] `ControlPlaneClient` (fail-safe REST client)
- [ ] `AgentContext` (correlation + execution ID propagation, async-safe)
- [ ] `AecpAgent` façade (`register`, `executeAction`, `heartbeat`, `shutdown`)
- [ ] Fail-safe publish (MQ errors must never crash the agent)
- [ ] Tests for policy enforcement and in-memory publisher

---

## Step-by-Step

### 1. Define the event models

Map each JSON Schema in `common/schema/` to native language types. All events must:
- Include the 5 base fields: `event_id` (UUID), `event_type`, `schema_version`, `timestamp`, `correlation_id`
- Serialize to JSON matching the schema exactly
- Be constructable with minimal boilerplate (use defaults where possible)

**Reference Python implementation**: [`sdk/python/aecp/events/`](../sdk/python/aecp/events/)

### 2. Implement EventPublisher

```
interface EventPublisher {
    publish(event: BaseEvent): void       // must not throw
    publishBatch(events: BaseEvent[]): void
    shutdown(): void
}
```

Requirements:
- **InMemoryPublisher**: thread-safe list + `getEvents()` for testing
- **KafkaPublisher**: partition by `agent_id`, retry ×3 with exponential backoff, DLQ on final failure
- All implementations: catch all exceptions internally, log only

**Reference Java implementation**: [`sdk/java/src/main/java/com/aecp/sdk/publisher/`](../sdk/java/src/main/java/com/aecp/sdk/publisher/)

### 3. Implement CredentialProvider

```
interface CredentialProvider {
    getServiceToken(serviceName: string): Token   // Token.isServiceAccount must be true
    isServiceAccount(tokenHint: string): boolean
}
```

Implementations:
- **MockProvider**: deterministic tokens keyed by service name, always `isServiceAccount=true`
- **VaultProvider**: placeholder — constructor accepts vault address + role_id, throws NotImplemented

### 4. Implement PolicyEnforcer

```
class PolicyEnforcer(policy: Policy) {
    enforceAction(action: string): void        // throw PolicyViolationError if not allowed
    enforceCredential(token: Token): void      // throw CRITICAL if not service account
    checkCostThreshold(usd: float): boolean    // return false if over limit (don't throw)
}
```

Policy loading: support `Policy.fromYaml(path)` and `Policy.fromDict(data)`. Wildcard `"*"` in `allowed_actions` means allow all (dev/test only).

### 5. Implement AgentContext

Context must propagate `correlation_id` and `execution_id` safely across:
- Thread pools (Java: `ThreadLocal`)
- Async/await coroutines (Python: `contextvars.ContextVar`)
- Callback-based async (Node.js: `AsyncLocalStorage`)

`newExecution()` must create a child scope with a fresh `execution_id` and restore the parent on exit.

### 6. Implement ControlPlaneClient

Three operations, all fail-safe (log warning + continue on any error):
- `registerAgent(event)` → `POST /agents/register`
- `getPolicy(agentId)` → `GET /policies/{id}` (returns null on 404)
- `reportViolation(event)` → `POST /violations`

Timeout: 5 seconds. Run async where possible to avoid blocking agent threads.

### 7. Implement AecpAgent

The main façade wires everything together:

```
class AecpAgent(config, publisher, credentialProvider, policyEnforcer) {
    register(): void
    executeAction(action, work): T
    heartbeat(): void
    startHeartbeat(): void   // background timer
    shutdown(): void
}
```

`executeAction` flow:
1. `AgentContext.newExecution()`
2. `policyEnforcer.enforceAction(action)` → on violation: emit SecurityEvent, re-throw
3. Record `timestamp_start`
4. Execute `work()`
5. Record `timestamp_end`, compute `latency_ms`
6. Emit `ExecutionEvent` asynchronously (non-blocking)
7. Return result (or re-throw exception from work)

### 8. Register with the decorator/instrumentation system (optional)

For decorator-style SDKs (Python, TypeScript):
- Register the publisher and enforcer in a module-level registry keyed by `agent_id`
- Decorators look up by `AgentContext.current().agentId` at call time

For Java/Go-style:
- Use explicit `agent.executeAction(...)` wrapping

### 9. Write tests

Minimum required tests:
- `PolicyEnforcer`: allowed action passes, blocked action throws, user credential throws CRITICAL
- `InMemoryPublisher`: concurrent publishes don't lose events
- `@agent_action` / equivalent: emits ExecutionEvent on success, SecurityEvent on violation
- `@track_api_usage` / equivalent: emits ApiUsageEvent with correct token count
- Fail-safe publish: broken publisher does not crash the agent

---

## Naming Conventions

Follow the existing SDK naming conventions for discoverability:

| Concept | Java | Python |
|---|---|---|
| Main agent | `AecpAgent` | `AecpAgent` |
| Config | `AgentConfig` | `AgentConfig` |
| Context | `AgentContext` | `AgentContext` |
| Publisher base | `EventPublisher` (interface) | `EventPublisher` (ABC) |
| Kafka publisher | `KafkaEventPublisher` | `KafkaEventPublisher` |
| In-memory publisher | `InMemoryEventPublisher` | `InMemoryEventPublisher` |
| Credential base | `CredentialProvider` (interface) | `CredentialProvider` (ABC) |
| Mock credentials | `MockCredentialProvider` | `MockCredentialProvider` |
| Policy error | `PolicyViolationException` | `PolicyViolationError` |
| Action decorator | n/a (use `executeAction`) | `@agent_action` |
| Usage decorator | n/a (emit manually) | `@track_api_usage` |

---

## Verification

Run the reference examples to validate your SDK produces the expected events:

```bash
# Expected: 1 registration, 2+ execution, 1+ api_usage, 1 security, 1 heartbeat events
python examples/python/jira_agent.py
```

Ensure your SDK produces JSON output that validates against the schemas in `common/schema/`.
