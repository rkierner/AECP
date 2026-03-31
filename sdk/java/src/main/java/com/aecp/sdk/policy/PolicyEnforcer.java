package com.aecp.sdk.policy;

import com.aecp.sdk.credential.Token;

/**
 * Stateless policy enforcer.
 *
 * <p>Validates actions and credentials against the agent's registered {@link Policy}.
 * The SDK calls this before every action — enforcement happens at the call site,
 * not in a central gateway, for minimal latency and maximum reliability.
 */
public class PolicyEnforcer {

    private final Policy policy;

    public PolicyEnforcer(Policy policy) {
        this.policy = policy;
    }

    /**
     * Throw {@link PolicyViolationException} if the action is not in the allowlist.
     * Wildcard {@code "*"} grants all actions — use only in dev/test.
     */
    public void enforceAction(String action) {
        var allowed = policy.getAllowedActions();
        if (allowed.contains("*") || allowed.contains(action)) {
            return;
        }
        throw new PolicyViolationException(
                String.format("Action '%s' is not permitted for agent '%s'. Allowed: %s",
                        action, policy.getAgentId(), allowed),
                "unauthorized_action",
                "HIGH"
        );
    }

    /**
     * Throw {@link PolicyViolationException} if the token is not a service account credential.
     */
    public void enforceCredential(Token token) {
        if (!token.isServiceAccount()) {
            throw new PolicyViolationException(
                    "User credentials detected. Only service account tokens are permitted. "
                    + "Use a CredentialProvider to obtain service tokens.",
                    "user_credential_detected",
                    "CRITICAL"
            );
        }
    }

    /**
     * Returns {@code true} if accumulated cost is within the daily limit.
     * Returns {@code false} (does NOT throw) — caller decides whether to block.
     */
    public boolean checkCostThreshold(double accumulatedCostUsd) {
        return accumulatedCostUsd <= policy.getDailyCostLimitUsd();
    }

    public Policy getPolicy() { return policy; }
}
