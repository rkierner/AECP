"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { AgentTableRow } from "./AgentTableRow";
import { RegisterAgentModal } from "./RegisterAgentModal";
import { useAgents } from "@/hooks/useAgents";
import { useViolations } from "@/hooks/useViolations";
import { useLiveEventStream } from "@/hooks/useLiveEventStream";
import type { HeartbeatEvent, ApiUsageEvent } from "@/types/events";

export function AgentTable() {
  const [showRegister, setShowRegister] = useState(false);
  const { data: agents = [], isLoading } = useAgents();
  const { data: violations = [] } = useViolations();
  const { events } = useLiveEventStream();

  // Build per-agent derived data from live event stream
  const today = new Date().toISOString().slice(0, 10);

  const latestHeartbeats: Record<string, HeartbeatEvent> = {};
  const eventsByAgent: Record<string, number> = {};
  const spendByAgent: Record<string, number> = {};

  for (const event of events) {
    if (event.event_type === "agent.heartbeat") {
      const hb = event as HeartbeatEvent;
      const existing = latestHeartbeats[hb.agent_id];
      if (!existing || hb.timestamp > existing.timestamp) {
        latestHeartbeats[hb.agent_id] = hb;
      }
    }
    if (
      "agent_id" in event &&
      event.timestamp.startsWith(today)
    ) {
      const aid = (event as { agent_id: string }).agent_id;
      eventsByAgent[aid] = (eventsByAgent[aid] ?? 0) + 1;
      if (event.event_type === "agent.api_usage") {
        const usage = event as ApiUsageEvent;
        spendByAgent[aid] = (spendByAgent[aid] ?? 0) + usage.estimated_cost_usd;
      }
    }
  }

  // Violations today per agent
  const violationsByAgent: Record<string, number> = {};
  for (const v of violations) {
    if (v.timestamp.startsWith(today)) {
      violationsByAgent[v.agent_id] = (violationsByAgent[v.agent_id] ?? 0) + 1;
    }
  }

  return (
    <>
      <Card>
        <CardHeader className="flex flex-row items-start justify-between">
          <div>
            <CardTitle>Registered Agents</CardTitle>
            <CardDescription className="text-xs mt-0.5">
              Monitor and manage your AI agents
            </CardDescription>
          </div>
          <Button size="sm" onClick={() => setShowRegister(true)}>
            Register Agent
          </Button>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Agent</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Last Heartbeat</TableHead>
                <TableHead>Events</TableHead>
                <TableHead>Daily Spend</TableHead>
                <TableHead className="text-center">Violations</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                Array.from({ length: 3 }).map((_, i) => (
                  <TableRow key={i}>
                    {Array.from({ length: 7 }).map((_, j) => (
                      <td key={j} className="px-4 py-3">
                        <div className="h-4 animate-pulse rounded bg-muted" />
                      </td>
                    ))}
                  </TableRow>
                ))
              ) : agents.length === 0 ? (
                <TableRow>
                  <td colSpan={7} className="text-center py-8 text-muted-foreground text-sm">
                    No agents registered yet
                  </td>
                </TableRow>
              ) : (
                agents.map((agent) => (
                  <AgentTableRow
                    key={agent.agent_id}
                    agent={agent}
                    lastHeartbeat={latestHeartbeats[agent.agent_id]}
                    eventsToday={eventsByAgent[agent.agent_id] ?? 0}
                    dailySpend={spendByAgent[agent.agent_id] ?? 0}
                    dailyBudget={100}
                    violationsToday={violationsByAgent[agent.agent_id] ?? 0}
                  />
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
      <RegisterAgentModal open={showRegister} onClose={() => setShowRegister(false)} />
    </>
  );
}
