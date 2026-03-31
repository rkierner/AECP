export type EventType =
  | "agent.registration"
  | "agent.execution"
  | "agent.api_usage"
  | "agent.security"
  | "agent.heartbeat";

export interface BaseEvent {
  event_id: string;
  event_type: EventType;
  schema_version: string;
  timestamp: string; // ISO 8601
  correlation_id: string;
}

export interface RegistrationEvent extends BaseEvent {
  event_type: "agent.registration";
  agent_id: string;
  runtime: string;
  version: string;
  owner: string;
  capabilities: string[];
  permissions_requested: string[];
}

export interface ExecutionEvent extends BaseEvent {
  event_type: "agent.execution";
  agent_id: string;
  execution_id: string;
  timestamp_start: string;
  timestamp_end: string | null;
  action: string;
  status: "success" | "failure" | "timeout" | "blocked";
  latency_ms: number | null;
  error_message: string | null;
}

export interface ApiUsageEvent extends BaseEvent {
  event_type: "agent.api_usage";
  agent_id: string;
  execution_id: string;
  provider: string;
  tokens_used: number;
  estimated_cost_usd: number;
  model: string | null;
}

export interface SecurityEvent extends BaseEvent {
  event_type: "agent.security";
  agent_id: string;
  violation_type:
    | "user_credential_detected"
    | "unauthorized_action"
    | "rate_limit_exceeded"
    | "cost_limit_exceeded";
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  details: {
    message: string;
    blocked: boolean;
    action_attempted?: string;
    [key: string]: unknown;
  };
}

export interface HeartbeatEvent extends BaseEvent {
  event_type: "agent.heartbeat";
  agent_id: string;
  status: "healthy" | "degraded" | "unhealthy";
  last_seen: string;
  metadata: {
    uptime_seconds?: number;
    events_published?: number;
    publish_errors?: number;
  } | null;
}

export type AecpEvent =
  | RegistrationEvent
  | ExecutionEvent
  | ApiUsageEvent
  | SecurityEvent
  | HeartbeatEvent;
