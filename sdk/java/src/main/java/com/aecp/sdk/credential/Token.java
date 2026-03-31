package com.aecp.sdk.credential;

import java.time.Instant;

/**
 * Immutable credential token obtained from a {@link CredentialProvider}.
 * Never constructed directly by agent code.
 */
public record Token(
        String value,
        String serviceName,
        Instant expiresAt,
        boolean isServiceAccount
) {
    public boolean isExpired() {
        return Instant.now().isAfter(expiresAt);
    }
}
