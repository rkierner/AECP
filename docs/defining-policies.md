# Defining Agent Policies

Policies govern what each agent is allowed to do. They are YAML files stored in `control-plane/policies/` — one file per agent.

---

## Policy File Reference

```yaml
# Required: must match the agent_id the agent registers with
agent_id: my-agent

# Actions this agent is allowed to perform.
# Use dot-notation: <service>.<operation>
# Wildcard "*" allows all actions — NEVER use in production.
allowed_actions:
  - jira.create_ticket
  - jira.search_issues
  - openai.chat_completion

# Credential requirements.
# Only "service_account_only" is currently supported.
credentials:
  type: service_account_only

# Cost controls — enforced by the SDK before each API call
cost_limits:
  daily_usd: 50.0       # Maximum spend per day (USD). Defaults to 100.0.

# Rate limits — checked by the SDK (enforcement is best-effort without a rate limiter)
rate_limits:
  requests_per_minute: 100   # Defaults to 1000.
```

---

## Field Reference

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `agent_id` | string | yes | — | Must exactly match the agent's self-reported `agent_id` |
| `allowed_actions` | string[] | no | `[]` | Dot-notation action allowlist. Empty list = deny all. |
| `credentials.type` | string | no | `service_account_only` | Only service accounts permitted |
| `cost_limits.daily_usd` | float | no | `100.0` | Daily spending cap in USD |
| `rate_limits.requests_per_minute` | int | no | `1000` | Rate limit (advisory in SDK v1) |

---

## Naming Actions

Actions follow `<service>.<operation>` dot-notation. Use consistent naming across your organization:

```
jira.create_ticket
jira.search_issues
jira.update_ticket
jira.add_comment

openai.chat_completion
anthropic.messages_create
aws.s3.get_object

github.create_pr
github.merge_pr
```

The SDK matches against the exact string. Wildcards are not supported in allowlists — only the special `"*"` value grants all permissions.

---

## Loading Policies

### Control Plane (automatic)

Place YAML files in `control-plane/policies/`. They are loaded at startup and served via:

```
GET /policies/{agent_id}
```

The SDK fetches this URL on `agent.register()` if a Control Plane URL is configured.

### SDK (local fallback)

Load directly from a file in your agent:

```python
# Python
from aecp.policy.models import Policy
from aecp.policy.enforcer import PolicyEnforcer

policy = Policy.from_yaml("policies/my-agent.yaml")
enforcer = PolicyEnforcer(policy)
```

```java
// Java
Policy policy = Policy.fromYaml(Path.of("policies/my-agent.yaml"));
PolicyEnforcer enforcer = new PolicyEnforcer(policy);
```

### Permissive (dev/test only)

```python
policy = Policy.permissive("my-agent")  # allows ALL actions
```

```java
Policy policy = Policy.permissive("my-agent");
```

---

## Violation Behavior

When a policy is violated, the SDK:
1. **Blocks** the action (raises `PolicyViolationError` / `PolicyViolationException`)
2. **Emits** a `SecurityEvent` to the MQ with the violation details
3. **Reports** the violation to the Control Plane via `POST /violations`

### Violation Types

| `violation_type` | Trigger | Default Severity |
|---|---|---|
| `unauthorized_action` | Action not in `allowed_actions` | `HIGH` |
| `user_credential_detected` | Non-service-account token detected | `CRITICAL` |
| `rate_limit_exceeded` | Rate limit breached | `MEDIUM` |
| `cost_limit_exceeded` | Daily cost cap reached | `HIGH` |

---

## Policy Updates

In v1, policy changes require a **control plane restart** to take effect. Hot reload is noted as a future enhancement (watchdog-based file monitoring).

For zero-downtime policy updates, use the Control Plane's `/policies/{agent_id}` endpoint as the source of truth, and poll it periodically in your agent's initialization logic.

---

## Example: Minimal Restrictive Policy

```yaml
agent_id: read-only-agent
allowed_actions:
  - jira.search_issues
  - confluence.search_pages
credentials:
  type: service_account_only
cost_limits:
  daily_usd: 5.0
```

## Example: LLM Agent Policy

```yaml
agent_id: summarization-agent
allowed_actions:
  - openai.chat_completion
  - anthropic.messages_create
  - confluence.get_page
credentials:
  type: service_account_only
cost_limits:
  daily_usd: 200.0
rate_limits:
  requests_per_minute: 30
```
