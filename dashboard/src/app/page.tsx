import { DashboardHeader } from "@/components/layout/DashboardHeader";
import { StatCardGrid } from "@/components/stats/StatCardGrid";
import { EventVolumeChart } from "@/components/charts/EventVolumeChart";
import { CostByAgentChart } from "@/components/charts/CostByAgentChart";
import { AgentTable } from "@/components/agents/AgentTable";
import { LiveEventStream } from "@/components/events/LiveEventStream";
import { ControlPlaneStatus } from "@/components/ControlPlaneStatus";

export default function DashboardPage() {
  return (
    <main className="min-h-screen bg-background">
      <div className="mx-auto max-w-screen-2xl px-4 sm:px-6 lg:px-8 py-6">
        <DashboardHeader />
        <ControlPlaneStatus />
        <StatCardGrid />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
          <EventVolumeChart />
          <CostByAgentChart />
        </div>
        <div className="mb-6">
          <AgentTable />
        </div>
        <LiveEventStream />
      </div>
    </main>
  );
}
