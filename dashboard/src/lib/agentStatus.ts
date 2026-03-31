import type { AgentStatus } from "@/types/agents";
import type { HeartbeatEvent } from "@/types/events";

/**
 * Derives display status from heartbeat data.
 *
 * Rules (matching the screenshot):
 *  - No heartbeat ever, or last heartbeat > 5 min ago → "offline"
 *  - heartbeat.status = "unhealthy"                   → "unhealthy" (renders as "Critical")
 *  - heartbeat.status = "degraded"                    → "degraded"
 *  - heartbeat.status = "healthy"                     → "healthy"
 */
export function deriveAgentStatus(
  lastHeartbeat: HeartbeatEvent | undefined
): AgentStatus {
  if (!lastHeartbeat) return "offline";

  const ts = new Date(lastHeartbeat.timestamp);
  const ageSeconds = (Date.now() - ts.getTime()) / 1000;
  if (ageSeconds > 300) return "offline";

  return lastHeartbeat.status as AgentStatus;
}

export function statusLabel(status: AgentStatus): string {
  switch (status) {
    case "healthy":
      return "Healthy";
    case "degraded":
      return "Degraded";
    case "unhealthy":
      return "Critical";
    case "offline":
      return "Offline";
  }
}

export function statusColor(status: AgentStatus): string {
  switch (status) {
    case "healthy":
      return "success";
    case "degraded":
      return "warning";
    case "unhealthy":
      return "destructive";
    case "offline":
      return "secondary";
  }
}
