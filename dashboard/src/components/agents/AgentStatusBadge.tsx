import { Badge } from "@/components/ui/badge";
import { statusLabel } from "@/lib/agentStatus";
import type { AgentStatus } from "@/types/agents";
import { cn } from "@/lib/utils";

interface AgentStatusBadgeProps {
  status: AgentStatus;
}

const variantClasses: Record<AgentStatus, string> = {
  healthy:
    "bg-green-100 text-green-800 border-green-200 dark:bg-green-900/30 dark:text-green-400 dark:border-green-800",
  degraded:
    "bg-yellow-100 text-yellow-800 border-yellow-200 dark:bg-yellow-900/30 dark:text-yellow-400 dark:border-yellow-800",
  unhealthy:
    "bg-red-100 text-red-800 border-red-200 dark:bg-red-900/30 dark:text-red-400 dark:border-red-800",
  offline:
    "bg-gray-100 text-gray-600 border-gray-200 dark:bg-gray-800/50 dark:text-gray-400 dark:border-gray-700",
};

export function AgentStatusBadge({ status }: AgentStatusBadgeProps) {
  return (
    <Badge
      variant="outline"
      className={cn("text-xs font-medium", variantClasses[status])}
    >
      {statusLabel(status)}
    </Badge>
  );
}
