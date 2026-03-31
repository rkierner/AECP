"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useEventHistory(limit = 50) {
  return useQuery({
    queryKey: ["event-history", limit],
    queryFn: () => api.events.list({ limit }),
    staleTime: Infinity, // used only for initial SSE hydration
  });
}
