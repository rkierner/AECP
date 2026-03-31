"use client";

import { MoreHorizontal } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { TableCell, TableRow } from "@/components/ui/table";
import { AgentStatusBadge } from "./AgentStatusBadge";
import { SpendProgressBar } from "./SpendProgressBar";
import { deriveAgentStatus } from "@/lib/agentStatus";
import { formatTimeSince, formatCount } from "@/lib/formatters";
import type { AgentMetadata, AgentStatus } from "@/types/agents";
import type { HeartbeatEvent } from "@/types/events";

interface AgentTableRowProps {
  agent: AgentMetadata;
  lastHeartbeat?: HeartbeatEvent;
  eventsToday: number;
  dailySpend: number;
  dailyBudget: number;
  violationsToday: number;
}

export function AgentTableRow({
  agent,
  lastHeartbeat,
  eventsToday,
  dailySpend,
  dailyBudget,
  violationsToday,
}: AgentTableRowProps) {
  const status: AgentStatus = deriveAgentStatus(lastHeartbeat);
  const heartbeatTime = lastHeartbeat?.timestamp ?? agent.last_seen;

  return (
    <TableRow>
      <TableCell>
        <div>
          <div className="font-medium text-sm">{agent.agent_id}</div>
          <div className="text-xs text-muted-foreground font-mono">{agent.agent_id}</div>
        </div>
      </TableCell>
      <TableCell>
        <AgentStatusBadge status={status} />
      </TableCell>
      <TableCell className="text-sm text-muted-foreground">
        {formatTimeSince(heartbeatTime)}
      </TableCell>
      <TableCell className="text-sm">{formatCount(eventsToday)}</TableCell>
      <TableCell>
        <SpendProgressBar current={dailySpend} budget={dailyBudget} />
      </TableCell>
      <TableCell className="text-sm text-center">
        {violationsToday > 0 ? (
          <span className="text-red-500 font-medium">{violationsToday}</span>
        ) : (
          <span className="text-muted-foreground">0</span>
        )}
      </TableCell>
      <TableCell>
        <DropdownMenu>
          <DropdownMenuTrigger>
            <Button variant="ghost" size="icon" className="h-7 w-7">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem>View Details</DropdownMenuItem>
            <DropdownMenuItem>View Policy</DropdownMenuItem>
            <DropdownMenuItem>View Violations</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </TableCell>
    </TableRow>
  );
}
