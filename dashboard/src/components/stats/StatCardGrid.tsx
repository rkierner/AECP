"use client";

import { Activity, AlertTriangle, DollarSign, Zap } from "lucide-react";
import { StatCard } from "./StatCard";
import { useDashboardStats } from "@/hooks/useDashboardStats";
import { formatCurrency, formatCount } from "@/lib/formatters";

export function StatCardGrid() {
  const { data: stats, isLoading } = useDashboardStats();

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <StatCard
        title="Active Agents"
        value={stats ? String(stats.active_agents) : "—"}
        delta={stats?.active_agents_delta}
        deltaPositive={stats ? !stats.active_agents_delta.startsWith("-") : undefined}
        icon={Activity}
        loading={isLoading}
      />
      <StatCard
        title="Events Today"
        value={stats ? formatCount(stats.events_today) : "—"}
        delta={stats?.events_today_delta}
        deltaPositive={stats ? !stats.events_today_delta.startsWith("-") : undefined}
        icon={Zap}
        loading={isLoading}
      />
      <StatCard
        title="Security Violations"
        value={stats ? String(stats.security_violations) : "—"}
        delta={stats?.violations_delta}
        deltaPositive={false}
        icon={AlertTriangle}
        loading={isLoading}
      />
      <StatCard
        title="Daily Spend"
        value={stats ? formatCurrency(stats.daily_spend_usd) : "—"}
        delta={
          stats
            ? `${stats.spend_delta} of ${formatCurrency(stats.spend_budget_usd)} budget`
            : undefined
        }
        deltaPositive={stats ? !stats.spend_delta.startsWith("-") : undefined}
        icon={DollarSign}
        loading={isLoading}
      />
    </div>
  );
}
