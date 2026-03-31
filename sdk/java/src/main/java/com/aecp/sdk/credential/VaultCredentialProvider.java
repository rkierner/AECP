package com.aecp.sdk.credential;

/**
 * HashiCorp Vault credential provider (placeholder).
 *
 * <p>Implementation steps:
 * <ol>
 *   <li>Add {@code io.github.jopenlibs:vault-java-driver} to pom.xml
 *   <li>Authenticate via AppRole:
 *       <pre>
 *         VaultConfig config = new VaultConfig().address(vaultAddr).build();
 *         Vault vault = new Vault(config);
 *         AuthResponse auth = vault.auth().loginByAppRole(roleId, secretId);
 *         String clientToken = auth.getAuthClientToken();
 *       </pre>
 *   <li>Read secret:
 *       <pre>
 *         LogicalResponse response = vault.logical().read("secret/data/aecp/" + serviceName);
 *         String tokenValue = response.getData().get("token");
 *       </pre>
 *   <li>Use vault lease TTL for {@code expiresAt}
 * </ol>
 *
 * <p>See: <a href="https://developer.hashicorp.com/vault/docs/auth/approle">Vault AppRole Auth</a>
 */
public class VaultCredentialProvider implements CredentialProvider {

    private final String vaultAddr;
    private final String roleId;
    private final String secretId;

    public VaultCredentialProvider(String vaultAddr, String roleId, String secretId) {
        this.vaultAddr = vaultAddr;
        this.roleId = roleId;
        this.secretId = secretId;
        // TODO: Initialize vault client and authenticate
    }

    @Override
    public Token getServiceToken(String serviceName) {
        throw new UnsupportedOperationException(
                "VaultCredentialProvider is not yet implemented. "
                + "See class Javadoc for step-by-step implementation guidance."
        );
    }

    @Override
    public boolean isServiceAccount(String tokenHint) {
        throw new UnsupportedOperationException("VaultCredentialProvider is not yet implemented.");
    }
}
