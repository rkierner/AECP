# AECP Architecture

## Overview

The Agent Execution Control Plane (AECP) is a lightweight observability and governance layer for agentic AI workloads. It uses a **push-based, runtime-agnostic** design: agents emit structured events to a central message queue, where they can be consumed by any downstream observability platform.

The Control Plane is a sidecar REST service — not in the hot path. Agents function fully even when it is unreachable.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AGENT RUNTIME                               │
│                                                                     │
│  ┌──────────────┐    ┌──────────────────────────────────────────┐  │
│  │  Agent Code  │───▶│              AECP SDK                    │  │
│  │ (Java/Python)│    │                                          │  │
│  └──────────────┘    │  ┌─────────────┐  ┌──────────────────┐  │  │
│                      │  │ AgentContext │  │  PolicyEnforcer  │  │  │
│                      │  │ (correlation,│  │  (action, cred,  │  │  │
│                      │  │  execution  │  │   cost limits)   │  │  │
│                      │  │  IDs)        │  └────────┬─────────┘  │  │
│                      │  └─────────────┘           │ on violation│  │
│                      │                            ▼             │  │
│                      │  ┌──────────────────────────────────┐   │  │
│                      │  │       EventPublisher             │   │  │
│                      │  │  (KafkaEventPublisher /          │   │  │
│                      │  │   InMemoryEventPublisher)        │   │  │
│                      │  └──────────────┬───────────────────┘   │  │
│                      │                 │ async, fail-safe       │  │
│                      │  ┌──────────────▼───────────────────┐   │  │
│                      │  │     CredentialProvider           │   │  │
│                      │  │  (Mock / Vault / IAM)            │   │  │
│                      │  └──────────────────────────────────┘   │  │
│                      └───────────────────┬──────────────────────┘  │
│                                          │ REST (best-effort)       │
│                                          ▼                          │
│                          ┌──────────────────────────┐              │
│                          │   Control Plane API       │              │
│                          │   (FastAPI)               │              │
│                          │                           │              │
│                          │  POST /agents/register    │              │
│                          │  GET  /policies/{id}      │              │
│                          │  POST /violations         │              │
│                          │  GET  /health             │              │
│                          └──────────────────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
                                     │
                        structured JSON events
                                     │
                    ┌────────────────▼─────────────────┐
                    │         Message Queue             │
                    │         (Kafka)                   │
                    │                                   │
                    │  Topic: aecp.events               │
                    │    Partitioned by agent_id        │
                    │    event_type as discriminator    │
                    │                                   │
                    │  Topic: aecp.events.dlq           │
                    │    Failed publish retries         │
                    └────────────────┬─────────────────┘
                                     │
                    ┌────────────────▼─────────────────┐
                    │     Observability Platform        │
                    │  (New Relic / Datadog / Splunk /  │
                    │   custom Kafka consumer)          │
                    └──────────────────────────────────┘

Policy Store (YAML files on disk or fetched from Control Plane)
  ├── Loaded at startup
  ├── Fetched per-agent by SDK on init
  └── Enforced in SDK before every action
```

---

## Component Details

### Agent SDK (Java / Python)

The SDK is the primary instrumentation layer. It is:
- **Lightweight**: pydantic + structlog in Python; Jackson + OkHttp in Java
- **Fail-safe**: MQ publish failures are caught and logged — never propagated
- **Async-safe**: Python uses `contextvars` (not `threading.local`) for coroutine safety

Key classes:

| Class | Responsibility |
|---|---|
| `AecpAgent` | Main façade — register, execute, heartbeat, shutdown |
| `AgentContext` | Thread/coroutine-local correlation and execution IDs |
| `PolicyEnforcer` | Validates actions and credentials before execution |
| `EventPublisher` | Emits structured JSON events to MQ |
| `CredentialProvider` | Abstracts Vault/IAM; blocks raw token injection |
| `ControlPlaneClient` | Fail-safe HTTP client for Control Plane REST API |

### Control Plane

A FastAPI service that:
- Stores agent registrations in memory (SQLite upgrade path documented)
- Serves YAML-based policies per agent
- Accepts and logs security violation reports
- Exposes `/health` for load balancer checks

The Control Plane is **not** in the hot path. If it is unreachable, agents log a warning and continue. Policies can also be loaded from YAML files embedded with the agent.

### Message Queue (Kafka)

All telemetry flows through a single topic `aecp.events`, partitioned by `agent_id` for per-agent ordering. Downstream consumers filter by `event_type`.

Dead-letter topic `aecp.events.dlq` receives events that exhausted all retry attempts.

### Policy Engine

Policies are YAML files — human-readable and Git-versioned. Enforcement happens **in the SDK** before any external call is made, ensuring:
- Minimum latency (no gateway roundtrip)
- No single point of failure
- No bypass possible (SDK is the only path)

---

## Data Flow: Single Action Execution

```
1. Agent code calls executeAction("jira.create_ticket", work)
2. SDK: AgentContext.newExecution() → fresh execution_id
3. SDK: PolicyEnforcer.enforceAction() → blocks if not allowed, emits SecurityEvent
4. SDK: CredentialProvider.getServiceToken() → service account token
5. SDK: PolicyEnforcer.enforceCredential() → blocks if user credential, emits SecurityEvent
6. Agent work executes → calls external API
7. SDK: records timestamp_end, computes latency_ms
8. SDK: EventPublisher.publish(ExecutionEvent) → async, fail-safe
9. (If LLM call): SDK: EventPublisher.publish(ApiUsageEvent)
10. Result returned to caller
```

---

## Event Schema

All events share a common base (see `common/schema/base-event.schema.json`):
```json
{
  "event_id":       "uuid-v4",
  "event_type":     "agent.registration | agent.execution | ...",
  "schema_version": "1.0",
  "timestamp":      "ISO8601 UTC",
  "correlation_id": "uuid-v4"
}
```

Five event types are defined. See [common/schema/](../common/schema/) for full JSON Schema definitions.

---

## Security Model

| Threat | Mitigation |
|---|---|
| User credential injection | `CredentialProvider` enforces service accounts; raw tokens are blocked at SDK level with `CRITICAL` SecurityEvent |
| Unauthorized actions | `PolicyEnforcer.enforceAction()` blocks non-allowlisted actions before execution |
| Cost overruns | `PolicyEnforcer.checkCostThreshold()` + `ApiUsageEvent` for audit |
| Observability gaps | Heartbeat events detect silent agent failures |
| MQ failure | Fail-safe publish with retry + DLQ — agent never crashes |
