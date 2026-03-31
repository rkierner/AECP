"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";

interface RegisterAgentModalProps {
  open: boolean;
  onClose: () => void;
}

export function RegisterAgentModal({ open, onClose }: RegisterAgentModalProps) {
  const queryClient = useQueryClient();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    agent_id: "",
    runtime: "python",
    version: "1.0.0",
    owner: "",
    capabilities: "",
  });

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await api.agents.register({
        agent_id: form.agent_id.trim(),
        runtime: form.runtime,
        version: form.version.trim(),
        owner: form.owner.trim(),
        capabilities: form.capabilities
          ? form.capabilities.split(",").map((s) => s.trim()).filter(Boolean)
          : [],
      });
      queryClient.invalidateQueries({ queryKey: ["agents"] });
      onClose();
      setForm({ agent_id: "", runtime: "python", version: "1.0.0", owner: "", capabilities: "" });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Register Agent</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="agent_id">Agent ID</Label>
            <Input
              id="agent_id"
              name="agent_id"
              value={form.agent_id}
              onChange={handleChange}
              placeholder="my-agent"
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="runtime">Runtime</Label>
              <select
                id="runtime"
                name="runtime"
                value={form.runtime}
                onChange={handleChange}
                className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm"
              >
                <option value="python">Python</option>
                <option value="java">Java</option>
                <option value="node">Node</option>
                <option value="dotnet">.NET</option>
                <option value="go">Go</option>
              </select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="version">Version</Label>
              <Input
                id="version"
                name="version"
                value={form.version}
                onChange={handleChange}
                placeholder="1.0.0"
                required
              />
            </div>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="owner">Owner</Label>
            <Input
              id="owner"
              name="owner"
              value={form.owner}
              onChange={handleChange}
              placeholder="platform-team"
              required
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="capabilities">Capabilities (comma-separated)</Label>
            <Input
              id="capabilities"
              name="capabilities"
              value={form.capabilities}
              onChange={handleChange}
              placeholder="jira.create_ticket, search.web"
            />
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? "Registering…" : "Register"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
