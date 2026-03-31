import { Badge } from "@/components/ui/badge";
import type { EventType } from "@/types/events";
import { cn } from "@/lib/utils";

const labels: Record<EventType, string> = {
  "agent.execution": "Execution",
  "agent.api_usage": "API Usage",
  "agent.security": "Security",
  "agent.heartbeat": "Heartbeat",
  "agent.registration": "Registration",
};

const colorClasses: Record<EventType, string> = {
  "agent.execution":
    "bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900/30 dark:text-blue-400 dark:border-blue-800",
  "agent.api_usage":
    "bg-purple-100 text-purple-800 border-purple-200 dark:bg-purple-900/30 dark:text-purple-400 dark:border-purple-800",
  "agent.security":
    "bg-red-100 text-red-800 border-red-200 dark:bg-red-900/30 dark:text-red-400 dark:border-red-800",
  "agent.heartbeat":
    "bg-green-100 text-green-800 border-green-200 dark:bg-green-900/30 dark:text-green-400 dark:border-green-800",
  "agent.registration":
    "bg-gray-100 text-gray-700 border-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-700",
};

export function EventTypeBadge({ eventType }: { eventType: EventType }) {
  return (
    <Badge
      variant="outline"
      className={cn("text-xs font-medium shrink-0", colorClasses[eventType])}
    >
      {labels[eventType]}
    </Badge>
  );
}
