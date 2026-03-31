"""
AECP Python SDK

Makes agentic AI workloads observable, governed, secure, and cost-controlled.

Quickstart:
    from aecp import AecpAgent, AgentConfig
    from aecp.publisher import InMemoryEventPublisher
    from aecp.credential import MockCredentialProvider
    from aecp.policy import Policy, PolicyEnforcer
    from aecp.decorators import agent_action, track_api_usage

    config = AgentConfig(agent_id="my-agent", version="1.0.0", owner="my-team")
    publisher = InMemoryEventPublisher()
    credential_provider = MockCredentialProvider()
    policy = Policy.permissive("my-agent")  # Use from_yaml() in production
    enforcer = PolicyEnforcer(policy)

    agent = AecpAgent(config, publisher, credential_provider, enforcer)
    agent.register()

    @agent_action("my.action")
    def do_work():
        ...
"""

from .agent import AecpAgent
from .config import AgentConfig
from .context import AgentContext
from .decorators import agent_action, track_api_usage

__version__ = "1.0.0"
__all__ = ["AecpAgent", "AgentConfig", "AgentContext", "agent_action", "track_api_usage"]
