"""Tests for PolicyEnforcer and Policy."""

import pytest
from datetime import datetime, timezone, timedelta

from aecp.policy.models import Policy
from aecp.policy.enforcer import PolicyEnforcer, PolicyViolationError
from aecp.credential.token import Token


@pytest.fixture
def policy():
    return Policy(
        agent_id="test-agent",
        allowed_actions=["jira.create_ticket", "jira.search_issues"],
    )


@pytest.fixture
def enforcer(policy):
    return PolicyEnforcer(policy)


@pytest.fixture
def service_token():
    return Token(
        value="svc-test-token",
        service_name="jira",
        expires_at=datetime.now(tz=timezone.utc) + timedelta(hours=1),
        is_service_account=True,
    )


@pytest.fixture
def user_token():
    return Token(
        value="user-personal-token-abc",
        service_name="jira",
        expires_at=datetime.now(tz=timezone.utc) + timedelta(hours=1),
        is_service_account=False,
    )


class TestEnforceAction:
    def test_allowed_action_passes(self, enforcer):
        enforcer.enforce_action("jira.create_ticket")  # no exception

    def test_disallowed_action_raises(self, enforcer):
        with pytest.raises(PolicyViolationError) as exc_info:
            enforcer.enforce_action("jira.delete_project")
        assert exc_info.value.violation_type == "unauthorized_action"
        assert exc_info.value.severity == "HIGH"
        assert "jira.delete_project" in str(exc_info.value)

    def test_wildcard_allows_everything(self):
        policy = Policy(agent_id="dev-agent", allowed_actions=["*"])
        enforcer = PolicyEnforcer(policy)
        enforcer.enforce_action("anything.at.all")  # no exception

    def test_empty_allowlist_blocks_all(self):
        policy = Policy(agent_id="restricted-agent", allowed_actions=[])
        enforcer = PolicyEnforcer(policy)
        with pytest.raises(PolicyViolationError):
            enforcer.enforce_action("jira.create_ticket")


class TestEnforceCredential:
    def test_service_account_token_passes(self, enforcer, service_token):
        enforcer.enforce_credential(service_token)  # no exception

    def test_user_token_raises_critical(self, enforcer, user_token):
        with pytest.raises(PolicyViolationError) as exc_info:
            enforcer.enforce_credential(user_token)
        assert exc_info.value.violation_type == "user_credential_detected"
        assert exc_info.value.severity == "CRITICAL"


class TestCostThreshold:
    def test_within_limit(self, enforcer):
        assert enforcer.check_cost_threshold(49.99) is True

    def test_at_limit(self, enforcer):
        # Default policy has 100 USD daily limit
        policy = Policy.from_dict({
            "agent_id": "test",
            "cost_limits": {"daily_usd": 50.0},
        })
        e = PolicyEnforcer(policy)
        assert e.check_cost_threshold(50.0) is True

    def test_over_limit(self):
        policy = Policy.from_dict({
            "agent_id": "test",
            "cost_limits": {"daily_usd": 50.0},
        })
        e = PolicyEnforcer(policy)
        assert e.check_cost_threshold(50.01) is False


class TestPolicyFromYaml:
    def test_permissive_factory(self):
        p = Policy.permissive("my-agent")
        assert "*" in p.allowed_actions
        assert p.agent_id == "my-agent"

    def test_from_dict(self):
        p = Policy.from_dict({
            "agent_id": "x",
            "allowed_actions": ["foo.bar"],
            "cost_limits": {"daily_usd": 25.0},
        })
        assert p.cost_limits.daily_usd == 25.0
