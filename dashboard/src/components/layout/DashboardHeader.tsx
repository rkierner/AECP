"use client";

import { Moon, RefreshCw, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/lib/theme";
import { useQueryClient } from "@tanstack/react-query";

export function DashboardHeader() {
  const { theme, toggle } = useTheme();
  const queryClient = useQueryClient();

  function handleRefresh() {
    queryClient.invalidateQueries();
  }

  return (
    <div className="flex items-start justify-between mb-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Agent Control Plane</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          Monitor and manage your AI agents in real-time
        </p>
      </div>
      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm" className="gap-2" onClick={handleRefresh}>
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh
        </Button>
        <Button variant="outline" size="icon" onClick={toggle} aria-label="Toggle theme">
          {theme === "dark" ? (
            <Sun className="h-4 w-4" />
          ) : (
            <Moon className="h-4 w-4" />
          )}
        </Button>
      </div>
    </div>
  );
}
