import type { AgentMetadata, ViolationReport } from "@/types/agents";
import type { AecpEvent } from "@/types/events";
import type { DashboardStats } from "@/types/stats";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8080";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`);
  if (!res.ok) {
    throw new Error(`API ${path} returned ${res.status}`);
  }
  return res.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`API ${path} returned ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  agents: {
    list: () => get<AgentMetadata[]>("/agents"),
    get: (id: string) => get<AgentMetadata>(`/agents/${id}`),
    register: (body: {
      agent_id: string;
      runtime: string;
      version: string;
      owner: string;
      capabilities?: string[];
      permissions_requested?: string[];
    }) => post<{ agent_id: string; registered_at: string }>("/agents/register", body),
  },
  violations: {
    list: () => get<ViolationReport[]>("/violations"),
  },
  events: {
    list: (params?: { limit?: number; event_type?: string; agent_id?: string }) => {
      const qs = new URLSearchParams();
      if (params?.limit) qs.set("limit", String(params.limit));
      if (params?.event_type) qs.set("event_type", params.event_type);
      if (params?.agent_id) qs.set("agent_id", params.agent_id);
      const query = qs.toString() ? `?${qs}` : "";
      return get<AecpEvent[]>(`/events${query}`);
    },
    stats: () => get<DashboardStats>("/events/stats"),
    streamUrl: () => `${BASE_URL}/events/stream`,
  },
  health: () => get<{ status: string; agents_registered: number; policies_loaded: number }>("/health"),
};
