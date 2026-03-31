package com.aecp.sdk.publisher;

import com.aecp.sdk.events.BaseEvent;

import java.util.List;

/**
 * Contract for all AECP event publishers.
 *
 * <p>CONTRACT: All implementations MUST be fail-safe.
 * Exceptions must be caught internally and never propagated to agent code.
 * Observability infrastructure must never break agent functionality.
 */
public interface EventPublisher {

    /**
     * Publish a single event. Must not throw exceptions.
     */
    void publish(BaseEvent event);

    /**
     * Publish multiple events. Implementations may batch these for efficiency.
     * Must not throw exceptions.
     */
    void publishBatch(List<BaseEvent> events);

    /**
     * Flush pending events and release resources cleanly.
     * Called during agent shutdown.
     */
    void shutdown();
}
