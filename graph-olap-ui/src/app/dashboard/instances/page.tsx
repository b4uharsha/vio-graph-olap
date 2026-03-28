"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Plus,
  Server,
  Clock,
  Cpu,
  ExternalLink,
  Trash2,
  RefreshCw,
  Database,
} from "lucide-react";
import { listInstances, terminateInstance } from "@/lib/api";
import type { Instance } from "@/lib/mock-data";

type FilterTab = "all" | "running" | "starting" | "terminated";

const statusConfig: Record<
  Instance["status"],
  { bg: string; text: string; dot: string }
> = {
  running: { bg: "bg-green-500/15", text: "text-green-400", dot: "bg-green-400" },
  starting: { bg: "bg-yellow-500/15", text: "text-yellow-400", dot: "bg-yellow-400" },
  failed: { bg: "bg-red-500/15", text: "text-red-400", dot: "bg-red-400" },
  terminated: { bg: "bg-zinc-500/15", text: "text-zinc-400", dot: "bg-zinc-500" },
};

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const hours = Math.floor(diff / 3600000);
  if (hours < 1) return "Just now";
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export default function InstancesPage() {
  const [instances, setInstances] = useState<Instance[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<FilterTab>("all");
  const [toast, setToast] = useState<string | null>(null);

  const fetchInstances = useCallback(async () => {
    const data = await listInstances();
    setInstances(data);
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchInstances();
    // Auto-refresh every 10 seconds
    const interval = setInterval(fetchInstances, 10000);
    return () => clearInterval(interval);
  }, [fetchInstances]);

  function showToast(msg: string) {
    setToast(msg);
    setTimeout(() => setToast(null), 3000);
  }

  async function handleTerminate(id: string, name: string) {
    if (!confirm(`Terminate instance "${name}"?`)) return;
    try {
      await terminateInstance(id);
      setInstances((prev) =>
        prev.map((i) =>
          i.id === id ? { ...i, status: "terminated" as const } : i
        )
      );
      showToast(`Instance "${name}" terminated`);
    } catch {
      showToast("Failed to terminate instance (API unavailable)");
    }
  }

  const filtered =
    filter === "all"
      ? instances
      : instances.filter((i) => i.status === filter);

  const tabs: { key: FilterTab; label: string; count: number }[] = [
    { key: "all", label: "All", count: instances.length },
    { key: "running", label: "Running", count: instances.filter((i) => i.status === "running").length },
    { key: "starting", label: "Starting", count: instances.filter((i) => i.status === "starting").length },
    { key: "terminated", label: "Terminated", count: instances.filter((i) => i.status === "terminated").length },
  ];

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-zinc-100">Instances</h2>
          <p className="mt-1 text-sm text-zinc-400">
            Manage your graph database instances
          </p>
        </div>
        <Link
          href="/dashboard/instances/new"
          className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-500"
        >
          <Plus size={16} />
          Launch Instance
        </Link>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1 rounded-lg border border-zinc-800 bg-zinc-900 p-1">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setFilter(tab.key)}
            className={`flex items-center gap-2 rounded-md px-3 py-1.5 text-sm transition-colors ${
              filter === tab.key
                ? "bg-zinc-800 text-zinc-100"
                : "text-zinc-500 hover:text-zinc-300"
            }`}
          >
            {tab.label}
            <span
              className={`rounded-full px-1.5 py-0.5 text-xs ${
                filter === tab.key
                  ? "bg-zinc-700 text-zinc-300"
                  : "bg-zinc-800 text-zinc-500"
              }`}
            >
              {tab.count}
            </span>
          </button>
        ))}
      </div>

      {/* Loading */}
      {loading && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {[1, 2].map((i) => (
            <div
              key={i}
              className="h-48 animate-pulse rounded-xl border border-zinc-800 bg-zinc-900"
            />
          ))}
        </div>
      )}

      {/* Empty state */}
      {!loading && filtered.length === 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex flex-col items-center justify-center rounded-xl border border-dashed border-zinc-700 py-16"
        >
          <Server size={40} className="text-zinc-600" />
          <p className="mt-4 text-zinc-400">
            {filter === "all"
              ? "No instances yet. Launch your first instance to get started."
              : `No ${filter} instances.`}
          </p>
          {filter === "all" && (
            <Link
              href="/dashboard/instances/new"
              className="mt-4 flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500"
            >
              <Plus size={14} />
              Launch Instance
            </Link>
          )}
        </motion.div>
      )}

      {/* Instance cards */}
      {!loading && filtered.length > 0 && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {filtered.map((instance, idx) => {
            const status = statusConfig[instance.status];
            return (
              <motion.div
                key={instance.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
                className="group rounded-xl border border-zinc-800 bg-zinc-900 p-5 transition-colors hover:border-zinc-700"
              >
                {/* Top row */}
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-medium text-zinc-200">
                      {instance.name}
                    </h3>
                    <p className="mt-0.5 text-xs text-zinc-500">
                      {instance.mappingName}
                    </p>
                  </div>
                  <span
                    className={`flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${status.bg} ${status.text}`}
                  >
                    <span className={`h-1.5 w-1.5 rounded-full ${status.dot}`} />
                    {instance.status}
                  </span>
                </div>

                {/* Details */}
                <div className="mt-4 grid grid-cols-2 gap-3">
                  <div className="flex items-center gap-2 text-xs text-zinc-400">
                    <Database size={13} className="text-zinc-600" />
                    <span className="capitalize">{instance.wrapperType}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-zinc-400">
                    <Cpu size={13} className="text-zinc-600" />
                    {instance.cpuCores} cores
                  </div>
                  <div className="flex items-center gap-2 text-xs text-zinc-400">
                    <Server size={13} className="text-zinc-600" />
                    {instance.memory}
                  </div>
                  <div className="flex items-center gap-2 text-xs text-zinc-400">
                    <Clock size={13} className="text-zinc-600" />
                    TTL: {instance.ttl}h
                  </div>
                </div>

                <div className="mt-3 text-xs text-zinc-600">
                  Created {timeAgo(instance.createdAt)}
                </div>

                {/* Actions */}
                <div className="mt-4 flex gap-2 border-t border-zinc-800 pt-3">
                  {instance.status === "running" && (
                    <>
                      <Link
                        href="/dashboard/explorer"
                        className="flex items-center gap-1.5 rounded-md bg-blue-600/15 px-3 py-1.5 text-xs font-medium text-blue-400 transition-colors hover:bg-blue-600/25"
                      >
                        <ExternalLink size={12} />
                        Connect
                      </Link>
                      <button
                        className="flex items-center gap-1.5 rounded-md bg-zinc-800 px-3 py-1.5 text-xs font-medium text-zinc-300 transition-colors hover:bg-zinc-700"
                      >
                        <RefreshCw size={12} />
                        Extend TTL
                      </button>
                    </>
                  )}
                  {instance.status !== "terminated" && (
                    <button
                      onClick={() => handleTerminate(instance.id, instance.name)}
                      className="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium text-red-400 transition-colors hover:bg-red-500/10"
                    >
                      <Trash2 size={12} />
                      Terminate
                    </button>
                  )}
                </div>
              </motion.div>
            );
          })}
        </div>
      )}

      {/* Toast */}
      {toast && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="fixed bottom-6 right-6 rounded-lg border border-zinc-700 bg-zinc-800 px-4 py-3 text-sm text-zinc-200 shadow-xl"
        >
          {toast}
        </motion.div>
      )}
    </div>
  );
}
