"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useDashboardStats() {
  return useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: () => api.events.stats(),
    refetchInterval: 30_000,
    staleTime: 15_000,
  });
}
