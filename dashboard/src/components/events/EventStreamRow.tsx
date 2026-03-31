import { Activity, AlertTriangle, DollarSign, Heart, UserPlus } from "lucide-react";
import { EventTypeBadge } from "./EventTypeBadge";
import { formatTimeSince } from "@/lib/formatters";
import type { AecpEvent, ExecutionEvent, ApiUsageEvent, SecurityEvent } from "@/types/events";

const icons = {
  "agent.execution": Activity,
  "agent.api_usage": DollarSign,
  "agent.security": AlertTriangle,
  "agent.heartbeat": Heart,
  "agent.registration": UserPlus,
};

function eventDescription(event: AecpEvent): string {
  switch (event.event_type) {
    case "agent.execution": {
      const e = event as ExecutionEvent;
      return `${e.action} — ${e.status}${e.latency_ms ? ` (${e.latency_ms}ms)` : ""}`;
    }
    case "agent.api_usage": {
      const e = event as ApiUsageEvent;
      return `${e.provider}${e.model ? ` / ${e.model}` : ""} — ${e.tokens_used} tokens ($${e.estimated_cost_usd.toFixed(4)})`;
    }
    case "agent.security": {
      const e = event as SecurityEvent;
      return `${e.violation_type} [${e.severity}]${e.details.blocked ? " — blocked" : ""}`;
    }
    case "agent.heartbeat":
      return `Status: ${event.status}`;
    case "agent.registration":
      return `Registered (${event.runtime} v${event.version})`;
  }
}

interface EventStreamRowProps {
  event: AecpEvent;
}

export function EventStreamRow({ event }: EventStreamRowProps) {
  const Icon = icons[event.event_type];
  const agentId = "agent_id" in event ? (event as { agent_id: string }).agent_id : "unknown";

  return (
    <div className="flex items-start gap-3 px-4 py-3 border-b border-border last:border-0 hover:bg-muted/30 transition-colors">
      <div className="mt-0.5 p-1.5 rounded-full bg-muted">
        <Icon className="h-3.5 w-3.5 text-muted-foreground" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <EventTypeBadge eventType={event.event_type} />
          <span className="text-sm font-medium">{agentId}</span>
        </div>
        <p className="text-xs text-muted-foreground mt-0.5 truncate">
          {eventDescription(event)}
        </p>
        <p className="text-xs text-muted-foreground/60 mt-0.5 font-mono truncate">
          {event.correlation_id}
        </p>
      </div>
      <span className="text-xs text-muted-foreground shrink-0">
        {formatTimeSince(event.timestamp)}
      </span>
    </div>
  );
}
