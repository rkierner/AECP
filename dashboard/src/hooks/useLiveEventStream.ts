"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { AecpEvent } from "@/types/events";

const MAX_EVENTS = 100;

export function useLiveEventStream(initialEvents: AecpEvent[] = []) {
  const [events, setEvents] = useState<AecpEvent[]>(initialEvents);
  const [isPaused, setIsPaused] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const bufferRef = useRef<AecpEvent[]>([]);
  const pausedRef = useRef(false);

  // Keep pausedRef in sync so the EventSource handler reads it without stale closure
  useEffect(() => {
    pausedRef.current = isPaused;
  }, [isPaused]);

  // Seed with initial events once
  useEffect(() => {
    if (initialEvents.length > 0) {
      setEvents(initialEvents.slice(0, MAX_EVENTS));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // intentionally only on mount

  useEffect(() => {
    const source = new EventSource(api.events.streamUrl());

    source.onopen = () => setIsConnected(true);

    source.onmessage = (e) => {
      try {
        const event = JSON.parse(e.data) as AecpEvent;
        if (pausedRef.current) {
          bufferRef.current.unshift(event);
        } else {
          setEvents((prev) => [event, ...prev].slice(0, MAX_EVENTS));
        }
      } catch {
        // ignore malformed messages
      }
    };

    source.onerror = () => {
      setIsConnected(false);
      // EventSource auto-reconnects; this fires during every reconnect attempt
    };

    return () => {
      source.close();
      setIsConnected(false);
    };
  }, []);

  const togglePause = useCallback(() => {
    setIsPaused((prev) => {
      if (prev) {
        // Resuming — drain buffer into events list
        const buffered = bufferRef.current.splice(0);
        if (buffered.length > 0) {
          setEvents((current) => [...buffered, ...current].slice(0, MAX_EVENTS));
        }
      }
      return !prev;
    });
  }, []);

  return { events, isPaused, isConnected, togglePause };
}
