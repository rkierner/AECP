"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useAgents() {
  return useQuery({
    queryKey: ["agents"],
    queryFn: () => api.agents.list(),
    refetchInterval: 15_000,
    staleTime: 10_000,
  });
}
