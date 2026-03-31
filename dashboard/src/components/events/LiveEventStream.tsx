"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Pause, Play, Wifi, WifiOff } from "lucide-react";
import { EventStreamRow } from "./EventStreamRow";
import { useLiveEventStream } from "@/hooks/useLiveEventStream";
import { useEventHistory } from "@/hooks/useEventHistory";
import type { AecpEvent } from "@/types/events";

export function LiveEventStream() {
  const { data: initial = [] } = useEventHistory(50);
  const { events, isPaused, isConnected, togglePause } = useLiveEventStream(
    initial as AecpEvent[]
  );

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between pb-3">
        <div>
          <CardTitle className="flex items-center gap-2">
            Live Event Stream
            {isConnected ? (
              <Wifi className="h-4 w-4 text-green-500" />
            ) : (
              <WifiOff className="h-4 w-4 text-muted-foreground" />
            )}
          </CardTitle>
          <CardDescription className="text-xs mt-0.5">
            Real-time events from Kafka topic aecp.events
          </CardDescription>
        </div>
        <Button variant="outline" size="sm" onClick={togglePause} className="gap-1.5">
          {isPaused ? (
            <>
              <Play className="h-3.5 w-3.5" />
              Resume
            </>
          ) : (
            <>
              <Pause className="h-3.5 w-3.5" />
              Pause
            </>
          )}
        </Button>
      </CardHeader>
      <CardContent className="p-0">
        <div className="max-h-80 overflow-y-auto">
          {events.length === 0 ? (
            <div className="px-4 py-8 text-center text-sm text-muted-foreground">
              {isConnected ? "Waiting for events…" : "Connecting to event stream…"}
            </div>
          ) : (
            events.map((event) => (
              <EventStreamRow key={event.event_id} event={event} />
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}
