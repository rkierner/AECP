# Observability Platform Integration

AECP is designed to be **vendor-neutral**. All events flow to Kafka topics. Connect your observability platform by consuming those topics — no AECP code changes required.

---

## Event Topics

| Topic | Content | Partitioned By |
|---|---|---|
| `aecp.events` | All 5 event types | `agent_id` |
| `aecp.events.dlq` | Failed publish retries | n/a |

Filter by the `event_type` field:

```
agent.registration   — agent startup
agent.execution      — action results + latency
agent.api_usage      — LLM/API token consumption + cost
agent.security       — policy violations
agent.heartbeat      — liveness signals
```

---

## New Relic

### Option A: Kafka Connect (recommended)

Use the [New Relic Kafka Connect Sink](https://docs.newrelic.com/docs/infrastructure/host-integrations/host-integrations-list/kafka-integration/) to stream events from Kafka directly into New Relic Logs or Events.

```yaml
# kafka-connect-newrelic.json
{
  "name": "aecp-newrelic-sink",
  "config": {
    "connector.class": "io.confluent.kafka.connect.logs.NewRelicSinkConnector",
    "topics": "aecp.events",
    "newrelic.api.key": "${NEW_RELIC_LICENSE_KEY}",
    "newrelic.logs.endpoint": "https://log-api.newrelic.com/log/v1"
  }
}
```

### Option B: Custom consumer

Write a Kafka consumer that forwards events to the New Relic Log API:

```python
from confluent_kafka import Consumer
import httpx, json

consumer = Consumer({"bootstrap.servers": "localhost:9092", "group.id": "aecp-nr-forwarder"})
consumer.subscribe(["aecp.events"])

NR_ENDPOINT = "https://log-api.newrelic.com/log/v1"
NR_KEY = "YOUR_LICENSE_KEY"

while True:
    msg = consumer.poll(1.0)
    if msg and not msg.error():
        event = json.loads(msg.value())
        # Map AECP event fields to New Relic log attributes
        httpx.post(NR_ENDPOINT,
            headers={"X-License-Key": NR_KEY, "Content-Type": "application/json"},
            json=[{"message": event.get("event_type"), **event}]
        )
```

---

## Datadog

### Datadog Agent with Kafka input (via Logstash)

Configure Logstash with the Kafka input and Datadog output:

```yaml
# logstash-aecp.conf
input {
  kafka {
    bootstrap_servers => "localhost:9092"
    topics => ["aecp.events"]
    codec => json
  }
}

filter {
  mutate {
    add_field => {
      "ddtags" => "aecp:true,agent_id:%{agent_id},event_type:%{event_type}"
    }
  }
}

output {
  datadog_logs {
    api_key => "${DD_API_KEY}"
    host => "http-intake.logs.datadoghq.com"
    port => 443
    use_ssl => true
  }
}
```

### Datadog Metrics from api_usage events

Track `estimated_cost_usd` and `tokens_used` as custom metrics:

```python
from datadog_api_client.v1.api.metrics_api import MetricsApi
# Filter consumer for event_type == "agent.api_usage"
# Submit as: aecp.api_usage.tokens_used (gauge), aecp.api_usage.cost_usd (gauge)
# Tag with agent_id, provider, model
```

---

## Splunk

Use the [Splunk Kafka Connect Sink](https://splunkbase.splunk.com/app/4073/):

```properties
# splunk-kafka-connect.properties
connector.class=com.splunk.kafka.connect.SplunkSinkConnector
tasks.max=2
topics=aecp.events
splunk.hec.uri=https://your-splunk-hec-endpoint:8088
splunk.hec.token=YOUR_HEC_TOKEN
splunk.hec.json.event.formatted=true
```

Events arrive in Splunk as JSON events with `sourcetype=_json`. Search example:

```spl
index=aecp event_type="agent.security" severity="CRITICAL"
| table agent_id, violation_type, details.message, timestamp
| sort -timestamp
```

---

## Grafana + Loki (self-hosted)

Use [Vector](https://vector.dev/) as a lightweight Kafka → Loki pipeline:

```toml
# vector.toml
[sources.aecp_kafka]
type = "kafka"
bootstrap_servers = "localhost:9092"
group_id = "aecp-vector"
topics = ["aecp.events"]
decoding.codec = "json"

[transforms.add_labels]
type = "remap"
inputs = ["aecp_kafka"]
source = '''
  .agent_id = string!(.agent_id)
  .event_type = string!(.event_type)
'''

[sinks.loki]
type = "loki"
inputs = ["add_labels"]
endpoint = "http://localhost:3100"
labels.agent_id = "{{ agent_id }}"
labels.event_type = "{{ event_type }}"
encoding.codec = "json"
```

---

## Custom Consumer

For any platform not listed above, implement a simple consumer:

```python
from confluent_kafka import Consumer
import json

consumer = Consumer({
    "bootstrap.servers": "localhost:9092",
    "group.id": "aecp-custom-sink",
    "auto.offset.reset": "earliest",
})
consumer.subscribe(["aecp.events"])

while True:
    msg = consumer.poll(timeout=1.0)
    if msg is None or msg.error():
        continue

    event = json.loads(msg.value())
    event_type = event["event_type"]
    agent_id = event.get("agent_id", "unknown")
    correlation_id = event.get("correlation_id")

    # Route to your platform based on event_type
    if event_type == "agent.security":
        alert(event)
    elif event_type == "agent.api_usage":
        track_cost(agent_id, event["estimated_cost_usd"], event["tokens_used"])
    elif event_type == "agent.execution":
        record_latency(agent_id, event["action"], event["latency_ms"])
```

---

## Recommended Dashboards / Alerts

| Alert | Query |
|---|---|
| Security violation | `event_type == "agent.security" AND severity IN ("HIGH", "CRITICAL")` |
| Agent silent | No `agent.heartbeat` for `agent_id=X` in last 2 minutes |
| Cost threshold at 80% | `SUM(estimated_cost_usd) > daily_limit * 0.8` per agent per day |
| High action latency | `agent.execution WHERE latency_ms > 5000` |
| Elevated failure rate | `agent.execution WHERE status = "failure" / total > 5%` per 5-minute window |
