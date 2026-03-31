"""Tests for @agent_action and @track_api_usage decorators."""

import asyncio

import pytest

from aecp.agent import AecpAgent
from aecp.config import AgentConfig
from aecp.credential.mock_provider import MockCredentialProvider
from aecp.decorators import agent_action, track_api_usage
from aecp.policy.enforcer import PolicyEnforcer, PolicyViolationError
from aecp.policy.models import Policy
from aecp.publisher.in_memory_publisher import InMemoryEventPublisher


@pytest.fixture
def publisher():
    p = InMemoryEventPublisher()
    yield p
    p.clear()


@pytest.fixture
def agent(publisher):
    config = AgentConfig(
        agent_id="decorator-test-agent",
        version="1.0.0",
        owner="test",
        capabilities=["jira.create_ticket", "search.web"],
    )
    policy = Policy(
        agent_id="decorator-test-agent",
        allowed_actions=["jira.create_ticket", "search.web"],
    )
    enforcer = PolicyEnforcer(policy)
    a = AecpAgent(config, publisher, MockCredentialProvider(), enforcer)
    a.register()
    return a


class TestAgentAction:
    def test_success_emits_execution_event(self, agent, publisher):
        @agent_action("jira.create_ticket", agent_id="decorator-test-agent")
        def create_ticket():
            return {"id": "JIRA-123"}

        result = create_ticket()
        assert result == {"id": "JIRA-123"}

        executions = publisher.get_events_by_type("agent.execution")
        assert len(executions) == 1
        evt = executions[0]
        assert evt.action == "jira.create_ticket"  # type: ignore
        assert evt.status == "success"  # type: ignore
        assert evt.latency_ms is not None  # type: ignore

    def test_failure_emits_failure_event(self, agent, publisher):
        @agent_action("jira.create_ticket", agent_id="decorator-test-agent")
        def bad_action():
            raise ValueError("Jira is down")

        with pytest.raises(ValueError):
            bad_action()

        executions = publisher.get_events_by_type("agent.execution")
        assert executions[-1].status == "failure"  # type: ignore
        assert "Jira is down" in executions[-1].error_message  # type: ignore

    def test_policy_violation_emits_security_event(self, agent, publisher):
        @agent_action("jira.delete_project", agent_id="decorator-test-agent")
        def delete_project():
            return "deleted"

        with pytest.raises(PolicyViolationError):
            delete_project()

        security_events = publisher.get_events_by_type("agent.security")
        assert len(security_events) >= 1
        sec = security_events[-1]
        assert sec.violation_type == "unauthorized_action"  # type: ignore
        assert sec.details["blocked"] is True  # type: ignore

    def test_publisher_failure_does_not_crash_agent(self, agent):
        """A broken publisher must never prevent agent execution."""

        class BrokenPublisher(InMemoryEventPublisher):
            def publish(self, event):
                raise RuntimeError("MQ is down!")

        broken = BrokenPublisher()
        from aecp import decorators as reg
        reg._publisher_registry["decorator-test-agent"] = broken

        @agent_action("jira.create_ticket", agent_id="decorator-test-agent")
        def create_ticket():
            return "ok"

        result = create_ticket()
        assert result == "ok"  # Agent runs even with broken publisher

        # Restore
        reg._publisher_registry["decorator-test-agent"] = agent.publisher

    def test_async_action(self, agent, publisher):
        @agent_action("search.web", agent_id="decorator-test-agent")
        async def search(query: str):
            return f"results for {query}"

        result = asyncio.run(search("test query"))
        assert "test query" in result

        executions = publisher.get_events_by_type("agent.execution")
        assert executions[-1].status == "success"  # type: ignore


class TestTrackApiUsage:
    def test_openai_style_token_tracking(self, agent, publisher):
        class FakeUsage:
            total_tokens = 500

        class FakeResponse:
            usage = FakeUsage()

        @track_api_usage("openai", cost_per_1k_tokens=0.002, agent_id="decorator-test-agent")
        def call_openai():
            return FakeResponse()

        call_openai()

        api_events = publisher.get_events_by_type("agent.api_usage")
        evt = api_events[-1]
        assert evt.tokens_used == 500  # type: ignore
        assert abs(evt.estimated_cost_usd - 0.001) < 1e-9  # type: ignore
        assert evt.provider == "openai"  # type: ignore
        assert evt.token_type == "service_account"  # type: ignore

    def test_anthropic_style_token_tracking(self, agent, publisher):
        class FakeUsage:
            input_tokens = 200
            output_tokens = 300

        class FakeResponse:
            usage = FakeUsage()

        @track_api_usage("anthropic", cost_per_1k_tokens=0.003, agent_id="decorator-test-agent")
        def call_anthropic():
            return FakeResponse()

        call_anthropic()

        api_events = publisher.get_events_by_type("agent.api_usage")
        evt = api_events[-1]
        assert evt.tokens_used == 500  # type: ignore

    def test_zero_tokens_when_no_usage_info(self, agent, publisher):
        @track_api_usage("some-api", agent_id="decorator-test-agent")
        def call_api():
            return {"result": "ok"}  # no token info

        call_api()

        api_events = publisher.get_events_by_type("agent.api_usage")
        evt = api_events[-1]
        assert evt.tokens_used == 0  # type: ignore
        assert evt.estimated_cost_usd == 0.0  # type: ignore
