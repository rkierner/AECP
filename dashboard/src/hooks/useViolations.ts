"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useViolations() {
  return useQuery({
    queryKey: ["violations"],
    queryFn: () => api.violations.list(),
    refetchInterval: 30_000,
    staleTime: 15_000,
  });
}
