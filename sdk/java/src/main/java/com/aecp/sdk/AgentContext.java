package com.aecp.sdk;

import java.util.UUID;

/**
 * Thread-local ambient context carrier for correlation and execution IDs.
 *
 * <p>Use {@link #newExecution()} to enter an isolated execution scope.
 * The scope is automatically restored when the returned {@link ExecutionScope} is closed.
 *
 * <p>Example:
 * <pre>{@code
 * try (var scope = AgentContext.newExecution()) {
 *     String execId = AgentContext.current().executionId();
 *     // ... execute action ...
 * }
 * }</pre>
 */
public final class AgentContext {

    public record Context(String correlationId, String executionId, String agentId) {}

    private static final ThreadLocal<Context> CONTEXT = ThreadLocal.withInitial(
            () -> new Context(UUID.randomUUID().toString(), UUID.randomUUID().toString(), "")
    );

    private AgentContext() {}

    public static Context current() {
        return CONTEXT.get();
    }

    public static void setAgentId(String agentId) {
        Context c = CONTEXT.get();
        CONTEXT.set(new Context(c.correlationId(), c.executionId(), agentId));
    }

    /**
     * Enter a new execution scope with a fresh execution_id.
     * The parent context is restored when the returned scope is closed.
     */
    public static ExecutionScope newExecution() {
        return newExecution(null);
    }

    public static ExecutionScope newExecution(String correlationId) {
        Context parent = CONTEXT.get();
        Context child = new Context(
                correlationId != null ? correlationId : parent.correlationId(),
                UUID.randomUUID().toString(),
                parent.agentId()
        );
        CONTEXT.set(child);
        return new ExecutionScope(parent);
    }

    public static final class ExecutionScope implements AutoCloseable {
        private final Context parent;

        ExecutionScope(Context parent) {
            this.parent = parent;
        }

        @Override
        public void close() {
            CONTEXT.set(parent);
        }

        public Context context() {
            return AgentContext.current();
        }
    }
}
