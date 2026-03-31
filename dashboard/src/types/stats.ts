export interface EventVolumeBucket {
  hour: string; // ISO 8601 UTC
  count: number;
}

export interface DashboardStats {
  active_agents: number;
  active_agents_delta: string;
  events_today: number;
  events_today_delta: string;
  security_violations: number;
  violations_delta: string;
  daily_spend_usd: number;
  spend_budget_usd: number;
  spend_delta: string;
  event_volume_series: EventVolumeBucket[];
  cost_by_agent_series: Record<string, Record<string, number>>; // agent_id → {day_abbr → cost}
}
