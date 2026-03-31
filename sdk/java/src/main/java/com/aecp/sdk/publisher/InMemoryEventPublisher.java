package com.aecp.sdk.publisher;

import com.aecp.sdk.events.BaseEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.stream.Collectors;

/**
 * Thread-safe in-memory publisher for testing and local development.
 *
 * <p>Use {@link #getEvents()} to inspect published events in tests.
 */
public class InMemoryEventPublisher implements EventPublisher {

    private static final Logger log = LoggerFactory.getLogger(InMemoryEventPublisher.class);

    private final CopyOnWriteArrayList<BaseEvent> events = new CopyOnWriteArrayList<>();

    @Override
    public void publish(BaseEvent event) {
        events.add(event);
        log.debug("Event published in-memory: type={} id={}", event.getEventType(), event.getEventId());
    }

    @Override
    public void publishBatch(List<BaseEvent> batch) {
        events.addAll(batch);
        log.debug("Batch published in-memory: count={}", batch.size());
    }

    @Override
    public void shutdown() {
        // Nothing to flush for in-memory
    }

    /** Returns a snapshot of all published events. Thread-safe. */
    public List<BaseEvent> getEvents() {
        return new ArrayList<>(events);
    }

    /** Returns events filtered by event_type string. */
    public List<BaseEvent> getEventsByType(String eventType) {
        return events.stream()
                .filter(e -> eventType.equals(e.getEventType()))
                .collect(Collectors.toList());
    }

    /** Reset the event log. Useful between test cases. */
    public void clear() {
        events.clear();
    }
}
