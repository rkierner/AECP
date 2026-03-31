import type { DashboardStats } from "@/types/stats";
import { formatHour } from "./formatters";

export interface VolumeDataPoint {
  time: string;
  count: number;
}

export interface CostDataPoint {
  day: string;
  [agentId: string]: number | string;
}

const DAY_ABBRS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export function toVolumeData(stats: DashboardStats): VolumeDataPoint[] {
  return stats.event_volume_series.map((bucket) => ({
    time: formatHour(bucket.hour),
    count: bucket.count,
  }));
}

export function toCostData(
  stats: DashboardStats
): { data: CostDataPoint[]; agentIds: string[] } {
  const agentIds = Object.keys(stats.cost_by_agent_series);

  const data: CostDataPoint[] = DAY_ABBRS.map((day) => {
    const point: CostDataPoint = { day };
    for (const agentId of agentIds) {
      point[agentId] = stats.cost_by_agent_series[agentId]?.[day] ?? 0;
    }
    return point;
  });

  return { data, agentIds };
}

// Deterministic color palette for agents (cycles if > 6 agents)
export const CHART_COLORS = [
  "var(--color-chart-1)",
  "var(--color-chart-2)",
  "var(--color-chart-3)",
  "var(--color-chart-4)",
  "var(--color-chart-5)",
  "#22c55e",
];
