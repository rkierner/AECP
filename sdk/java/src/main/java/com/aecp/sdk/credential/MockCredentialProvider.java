package com.aecp.sdk.credential;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Map;
import java.util.Set;

/**
 * Deterministic mock for local development and testing.
 * All returned tokens are marked {@code isServiceAccount=true} with a 1-hour TTL.
 */
public class MockCredentialProvider implements CredentialProvider {

    private static final Map<String, String> SERVICE_TOKENS = Map.of(
            "jira",       "svc-jira-mock-abc123",
            "openai",     "svc-openai-mock-def456",
            "anthropic",  "svc-anthropic-mock-ghi789",
            "aws",        "svc-aws-mock-jkl012",
            "github",     "svc-github-mock-mno345"
    );

    private static final String DEFAULT_TOKEN = "svc-default-mock-xyz000";

    @Override
    public Token getServiceToken(String serviceName) {
        String value = SERVICE_TOKENS.getOrDefault(serviceName, DEFAULT_TOKEN);
        return new Token(
                value,
                serviceName,
                Instant.now().plus(1, ChronoUnit.HOURS),
                true
        );
    }

    @Override
    public boolean isServiceAccount(String tokenHint) {
        return SERVICE_TOKENS.containsValue(tokenHint) || DEFAULT_TOKEN.equals(tokenHint);
    }
}
