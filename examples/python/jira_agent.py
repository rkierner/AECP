#!/usr/bin/env python3
"""
AECP Example: Python Jira Agent
================================
Demonstrates the full AECP SDK lifecycle:
  1. Agent configuration and registration
  2. Policy-governed action execution via @agent_action decorator
  3. LLM token usage tracking via @track_api_usage decorator
  4. Policy violation detection and SecurityEvent emission
  5. Structured JSON event output

Run:
    pip install -r requirements.txt
    python jira_agent.py

To run against Kafka (requires docker-compose stack to be running):
    AECP_PUBLISHER_TYPE=kafka python jira_agent.py
"""

import json
import os
import time
from dataclasses import dataclass

from aecp import AecpAgent, AgentConfig, agent_action, track_api_usage
from aecp.credential import MockCredentialProvider
from aecp.policy import Policy, PolicyEnforcer, PolicyViolationError
from aecp.publisher import InMemoryEventPublisher, KafkaEventPublisher


# ── Configuration ─────────────────────────────────────────────────────────────

AGENT_ID = "example-python-agent"
PUBLISHER_TYPE = os.getenv("AECP_PUBLISHER_TYPE", "inmemory")
KAFKA_SERVERS = os.getenv("AECP_KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
CONTROL_PLANE_URL = os.getenv("AECP_CONTROL_PLANE_URL", "http://localhost:8080")


# ── Set up shared infrastructure ──────────────────────────────────────────────

def build_publisher():
    if PUBLISHER_TYPE == "kafka":
        print(f"[aecp] Using Kafka publisher ({KAFKA_SERVERS})")
        return KafkaEventPublisher(
            bootstrap_servers=KAFKA_SERVERS,
            topic="aecp.events",
            dlq_topic="aecp.events.dlq",
        )
    print("[aecp] Using in-memory publisher (set AECP_PUBLISHER_TYPE=kafka for Kafka)")
    return InMemoryEventPublisher()


publisher = build_publisher()

config = AgentConfig(
    agent_id=AGENT_ID,
    version="1.0.0",
    owner="platform-team",
    capabilities=["jira.create_ticket", "openai.chat_completion"],
    permissions_requested=["jira:write"],
    control_plane_url=CONTROL_PLANE_URL,
    publisher_type=PUBLISHER_TYPE,
)

# Load policy from the control plane if available; fall back to local YAML
policy = Policy(
    agent_id=AGENT_ID,
    allowed_actions=["jira.create_ticket", "openai.chat_completion", "search.web"],
)
enforcer = PolicyEnforcer(policy)
credential_provider = MockCredentialProvider()

agent = AecpAgent(config, publisher, credential_provider, enforcer)


# ── Simulated external services ────────────────────────────────────────────────

@dataclass
class JiraTicket:
    id: str
    summary: str
    status: str = "Open"


@dataclass
class LLMResponse:
    """Simulates an OpenAI-style response with token usage."""
    content: str

    class _Usage:
        total_tokens = 450

    usage = _Usage()


def _call_jira_api(summary: str, description: str) -> JiraTicket:
    """Simulates a Jira API call with realistic latency."""
    time.sleep(0.05)  # simulate 50ms network call
    return JiraTicket(id="DEMO-42", summary=summary)


def _call_openai_api(prompt: str) -> LLMResponse:
    """Simulates an LLM call returning an OpenAI-style response object."""
    time.sleep(0.1)  # simulate 100ms LLM call
    return LLMResponse(content=f"Suggested ticket description: {prompt[:50]}...")


# ── Agent actions using @agent_action decorator ────────────────────────────────
# The decorator handles policy enforcement, ExecutionEvent emission,
# and SecurityEvent emission on violations — all transparently.

@agent_action("jira.create_ticket", agent_id=AGENT_ID)
@track_api_usage("openai", cost_per_1k_tokens=0.002, agent_id=AGENT_ID)
def create_jira_ticket_with_ai(summary: str) -> JiraTicket:
    """
    Creates a Jira ticket, first using an LLM to generate a better description.
    Demonstrates chained decoration: policy check → execution tracking → usage tracking.
    """
    # Get service account credential — never a raw token
    token = credential_provider.get_service_token("jira")
    enforcer.enforce_credential(token)  # Explicit credential check

    # Call LLM to enrich description (token usage tracked by @track_api_usage)
    llm_response = _call_openai_api(f"Write a Jira ticket description for: {summary}")

    # Create the actual ticket
    ticket = _call_jira_api(summary, llm_response.content)
    return ticket


@agent_action("jira.create_ticket", agent_id=AGENT_ID)
def create_jira_ticket_simple(summary: str) -> JiraTicket:
    """Simple ticket creation without LLM enrichment."""
    token = credential_provider.get_service_token("jira")
    enforcer.enforce_credential(token)
    return _call_jira_api(summary, summary)


@agent_action("jira.delete_project", agent_id=AGENT_ID)
def delete_project_violating_policy(project_key: str) -> dict:
    """
    This action is NOT in the policy allowlist.
    The @agent_action decorator will block it and emit a SecurityEvent
    BEFORE this function body is ever reached.
    """
    return {"deleted": project_key}  # unreachable


# ── Main: run the agent and print all events ───────────────────────────────────

def main():
    print("=" * 70)
    print("AECP Python Example Agent")
    print("=" * 70)

    # Step 1: Register the agent
    print("\n[1] Registering agent with control plane...")
    agent.register()

    # Step 2: Execute a permitted action
    print("\n[2] Creating Jira ticket (permitted action)...")
    ticket = create_jira_ticket_simple("Fix login page timeout issue")
    print(f"    Created: {ticket.id} — {ticket.summary}")

    # Step 3: Execute with LLM usage tracking
    print("\n[3] Creating ticket with AI enrichment (chained decorators)...")
    ticket2 = create_jira_ticket_with_ai("Add dark mode support to dashboard")
    print(f"    Created: {ticket2.id} — {ticket2.summary}")

    # Step 4: Attempt a policy-violating action
    print("\n[4] Attempting unauthorized action (jira.delete_project)...")
    try:
        delete_project_violating_policy("MY-PROJECT")
    except PolicyViolationError as e:
        print(f"    Blocked as expected: {e}")

    # Step 5: Emit a heartbeat
    print("\n[5] Emitting heartbeat...")
    agent.heartbeat()

    # Step 6: Print all captured events
    if isinstance(publisher, InMemoryEventPublisher):
        events = publisher.get_events()
        print(f"\n{'=' * 70}")
        print(f"Captured {len(events)} events:")
        print(f"{'=' * 70}")

        for event in events:
            data = json.loads(event.to_json())
            print(f"\n[{data['event_type']}]")
            print(json.dumps(data, indent=2, default=str))

    # Shutdown
    agent.shutdown()
    print(f"\n{'=' * 70}")
    print("Agent shutdown complete.")


if __name__ == "__main__":
    main()
