package com.aecp.sdk.policy;

/**
 * Thrown when an agent attempts a policy-prohibited operation.
 * Carries machine-readable violationType and severity for SecurityEvent emission.
 */
public class PolicyViolationException extends RuntimeException {

    private final String violationType;
    private final String severity;

    public PolicyViolationException(String message, String violationType, String severity) {
        super(message);
        this.violationType = violationType;
        this.severity = severity;
    }

    public String getViolationType() { return violationType; }
    public String getSeverity() { return severity; }
}
