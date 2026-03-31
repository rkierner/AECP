"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ChartContainer } from "./ChartContainer";
import { useDashboardStats } from "@/hooks/useDashboardStats";
import { toCostData, CHART_COLORS } from "@/lib/chartData";

export function CostByAgentChart() {
  const { data: stats, isLoading } = useDashboardStats();
  const { data: chartData, agentIds } = stats
    ? toCostData(stats)
    : { data: [], agentIds: [] };

  return (
    <ChartContainer
      title="Cost by Agent"
      description="Weekly spending breakdown per agent (USD)"
      loading={isLoading}
    >
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={chartData} margin={{ top: 4, right: 4, left: -16, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-border" vertical={false} />
          <XAxis
            dataKey="day"
            tick={{ fontSize: 11 }}
            className="fill-muted-foreground"
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            tick={{ fontSize: 11 }}
            className="fill-muted-foreground"
            tickLine={false}
            axisLine={false}
            tickFormatter={(v) => `$${v}`}
          />
          <Tooltip
            formatter={(value) => [`$${Number(value).toFixed(2)}`, undefined]}
            contentStyle={{
              backgroundColor: "var(--color-card)",
              border: "1px solid var(--color-border)",
              borderRadius: "6px",
              fontSize: "12px",
            }}
          />
          <Legend wrapperStyle={{ fontSize: 11 }} />
          {agentIds.map((agentId, i) => (
            <Bar
              key={agentId}
              dataKey={agentId}
              stackId="cost"
              fill={CHART_COLORS[i % CHART_COLORS.length]}
              radius={i === agentIds.length - 1 ? [4, 4, 0, 0] : [0, 0, 0, 0]}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </ChartContainer>
  );
}
