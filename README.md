# Agent Execution Control Plane (AECP)

A production-ready platform for making agentic AI workloads **observable, governed, secure, and cost-controlled** across Java, Python, and other runtimes.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        AGENT RUNTIME                            │
│                                                                 │
│  ┌──────────────┐    ┌───────────────┐    ┌────────────────┐   │
│  │  Agent Code  │───▶│  AECP SDK     │───▶│ Control Plane  │   │
│  │ (Java/Python)│    │               │    │  REST API      │   │
│  └──────────────┘    │ • AgentContext│    │                │   │
│                      │ • PolicyEnf.  │    │ /agents/reg.   │   │
│                      │ • CredProv.   │    │ /policies/:id  │   │
│                      │ • Interceptor │    │ /violations    │   │
│                      │ • EventPub.   │    └────────────────┘   │
│                      └───────┬───────┘                         │
└──────────────────────────────┼──────────────────────────────────┘
                               │ structured JSON events
                               ▼
                    ┌─────────────────────┐
                    │   Message Queue     │
                    │  (Kafka)            │
                    │                     │
                    │  aecp.events        │
                    │  aecp.events.dlq    │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐         ┌─────────────────────┐
                    │  Observability      │         │  Dashboard          │
                    │  (New Relic /       │         │  (Next.js)          │
                    │   Datadog / etc.)   │         │  localhost:3000     │
                    └─────────────────────┘         └──────────┬──────────┘
                                                               │ REST + SSE
                                                    ┌──────────▼──────────┐
                                                    │  Control Plane      │
                                                    │  GET /events/stats  │
                                                    │  GET /events/stream │
                                                    └─────────────────────┘
```

## Repository Layout

```
AECP/
├── common/schema/        # Language-neutral JSON Schema event contracts
├── sdk/java/             # Java 17 SDK (Maven)
├── sdk/python/           # Python 3.11+ SDK (pip/setuptools)
├── control-plane/        # FastAPI control plane service
├── dashboard/            # Next.js real-time dashboard (port 3000)
├── examples/             # Runnable reference agents
├── docker-compose.yml    # Kafka + Control Plane + Dashboard local stack
└── docs/                 # Full documentation
```

---

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| Docker + Docker Compose | 24+ | [docker.com](https://www.docker.com/get-started) |
| Python | 3.9+ | `brew install python@3.12` |
| Java JDK | 17+ | `brew install openjdk@17` |
| Maven | 3.8+ | `brew install maven` |
| Node.js | 20+ | `brew install node` (dashboard only) |

> **Python note:** macOS ships with Python 3.9. The example uses a `run.sh` script that creates an isolated venv automatically — no manual `pip` needed.
>
> **Java note:** After installing the JDK via Homebrew, you may need to add it to your PATH:
> ```bash
> echo 'export PATH="/opt/homebrew/opt/openjdk@17/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc
> ```

---

## Quickstart

### 1. Start the local stack

```bash
docker-compose up -d
```

This starts:
- **Kafka** on `localhost:9092` (topics `aecp.events` and `aecp.events.dlq` auto-created)
- **Control Plane** on `http://localhost:8080`
- **Dashboard** on `http://localhost:3000`

Verify: `curl http://localhost:8080/health`

### 2. Run the Python example agent

```bash
cd examples/python
AECP_PUBLISHER_TYPE=kafka bash run.sh
```

`run.sh` creates an isolated venv, installs the SDK with the Kafka extra (`aecp-sdk[kafka]`), and runs the agent. Without `AECP_PUBLISHER_TYPE=kafka` the agent falls back to the in-memory publisher and no events will appear in Kafka.

### 3. Run the Java example agent

```bash
# Install the SDK into your local Maven repository first
mvn install -f sdk/java/pom.xml -DskipTests

# Then run the example in Kafka mode
cd examples/java/jira-agent
AECP_PUBLISHER_TYPE=kafka mvn compile exec:java
```

Without `AECP_PUBLISHER_TYPE=kafka` the agent falls back to the in-memory publisher and no events will appear in Kafka.

### 4. Observe events in Kafka

```bash
docker exec -it aecp-kafka kafka-console-consumer \
  --bootstrap-server kafka:29092 \
  --topic aecp.events \
  --from-beginning \
  --property print.key=true
```

> `kafka:29092` is the internal Docker network listener. Use this when running commands inside the container via `docker exec`. Use `localhost:9092` only when connecting from the host machine directly.

---

## Core Concepts

### Events

All agents emit structured JSON events to Kafka. Five event types are defined in `common/schema/`:

| Event Type | When Emitted |
|---|---|
| `agent.registration` | On agent startup |
| `agent.execution` | After every governed action |
| `agent.api_usage` | After every LLM/API call |
| `agent.security` | On policy violation detection |
| `agent.heartbeat` | Periodically (default 30s) |

Every event includes `event_id`, `correlation_id`, `timestamp`, and `schema_version`.

### Policies

Policies are YAML files in `control-plane/policies/`. Each file governs one agent:

```yaml
agent_id: my-agent
allowed_actions:
  - jira.create_ticket
credentials:
  type: service_account_only
cost_limits:
  daily_usd: 50.0
rate_limits:
  requests_per_minute: 100
```

See [docs/defining-policies.md](docs/defining-policies.md) for the full reference.

### Zero-Trust Credentials

Agents must use `CredentialProvider` — never raw token strings. The SDK blocks execution and emits a `CRITICAL` security event if a non-service-account credential is detected.

---

## Documentation

- [Architecture](docs/architecture.md)
- [Adding a New Runtime SDK](docs/adding-a-new-sdk.md)
- [Defining Policies](docs/defining-policies.md)
- [Observability Integration](docs/observability-integration.md)

---

## Dashboard

The dashboard provides a real-time view of all agents, events, and spending across the platform.

**Open `http://localhost:3000` after running `docker-compose up -d`.**

| Section | Description |
|---|---|
| Stat cards | Active agents, events today, security violations, daily spend vs. budget |
| Event Volume | Hourly execution + API call volume over the last 24 hours |
| Cost by Agent | Weekly spending breakdown per agent |
| Registered Agents | Live agent table with status, heartbeat age, spend progress bars, and violation counts |
| Live Event Stream | Real-time feed of all events from Kafka via SSE; supports pause/resume |

To run the dashboard in development mode (without Docker):

```bash
cd dashboard
npm install
npm run dev   # → http://localhost:3000
```

Requires the control plane to be running on `http://localhost:8080`. Theme (light/dark) is persisted per browser.

---

## Control Plane API

| Method | Path | Description |
|---|---|---|
| `POST` | `/agents/register` | Register an agent |
| `GET` | `/agents` | List all registered agents |
| `GET` | `/agents/{agent_id}` | Get agent metadata |
| `GET` | `/policies/{agent_id}` | Get agent policy |
| `POST` | `/violations` | Report a security violation |
| `GET` | `/violations` | List all reported violations |
| `GET` | `/events` | Recent event history |
| `GET` | `/events/stats` | Aggregated dashboard statistics |
| `GET` | `/events/stream` | Live event stream (SSE) |
| `GET` | `/health` | Health check |

Interactive docs: `http://localhost:8080/docs`
