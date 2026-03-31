package com.aecp.sdk.credential;

/**
 * Abstraction over secret stores (HashiCorp Vault, AWS IAM, GCP Workload Identity, etc.).
 *
 * <p>All credentials must flow through a registered CredentialProvider.
 * Agents must never inject raw token strings — the SDK blocks this
 * and emits a CRITICAL SecurityEvent if a violation is detected.
 */
public interface CredentialProvider {

    /**
     * Retrieve a service account token for the given service.
     *
     * @param serviceName Logical service identifier (e.g. "jira", "openai", "aws-s3")
     * @return A Token with {@code isServiceAccount() == true}
     * @throws RuntimeException if the provider cannot resolve a token
     */
    Token getServiceToken(String serviceName);

    /**
     * Returns true if the given token value is a known service account credential.
     * Used by the SDK to detect accidental user credential injection.
     */
    boolean isServiceAccount(String tokenHint);
}
