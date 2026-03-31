export interface AgentMetadata {
  agent_id: string;
  runtime: string;
  version: string;
  owner: string;
  capabilities: string[];
  permissions_requested: string[];
  registered_at: string; // ISO 8601
  last_seen: string | null; // ISO 8601
}

export type AgentStatus = "healthy" | "degraded" | "unhealthy" | "offline";

export interface AgentStatusSummary {
  agent_id: string;
  display_name: string;
  status: AgentStatus;
  last_heartbeat: string | null;
  events_today: number;
  daily_spend_usd: number;
  daily_budget_usd: number;
  violations_today: number;
}

export interface ViolationReport {
  agent_id: string;
  violation_type: string;
  severity: string;
  details: Record<string, unknown>;
  timestamp: string;
  correlation_id: string;
}
