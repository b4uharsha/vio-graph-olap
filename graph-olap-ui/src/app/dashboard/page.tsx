"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Server,
  Map,
  Search,
  Clock,
  Plus,
  Play,
  Compass,
  ArrowRight,
  Database,
  RefreshCw,
} from "lucide-react";
import { listInstances, listMappings } from "@/lib/api";
import { mockActivities } from "@/lib/mock-data";
import type { Instance, Mapping } from "@/lib/mock-data";

function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

function StatCard({
  label,
  value,
  icon: Icon,
  color,
  loading,
}: {
  label: string;
  value: string | number;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  color: string;
  loading?: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-zinc-800 bg-zinc-900 p-5"
    >
      <div className="flex items-center justify-between">
        <p className="text-sm text-zinc-400">{label}</p>
        <div className={`rounded-lg p-2 ${color}`}>
          <Icon size={18} />
        </div>
      </div>
      <div className="mt-3">
        {loading ? (
          <div className="h-8 w-20 animate-pulse rounded bg-zinc-800" />
        ) : (
          <p className="text-2xl font-bold text-zinc-100">{value}</p>
        )}
      </div>
    </motion.div>
  );
}

export default function DashboardPage() {
  const [instances, setInstances] = useState<Instance[]>([]);
  const [mappings, setMappings] = useState<Mapping[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      const [inst, maps] = await Promise.all([
        listInstances(),
        listMappings(),
      ]);
      setInstances(inst);
      setMappings(maps);
      setLoading(false);
    }
    load();
  }, []);

  const activeInstances = instances.filter((i) => i.status === "running").length;
  const today = new Date().toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <div className="mx-auto max-w-6xl space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-zinc-100">{getGreeting()}</h2>
        <p className="mt-1 text-sm text-zinc-400">{today}</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Active Instances"
          value={activeInstances}
          icon={Server}
          color="bg-green-500/15 text-green-400"
          loading={loading}
        />
        <StatCard
          label="Total Mappings"
          value={mappings.length}
          icon={Map}
          color="bg-blue-500/15 text-blue-400"
          loading={loading}
        />
        <StatCard
          label="Queries Today"
          value="1,247"
          icon={Search}
          color="bg-purple-500/15 text-purple-400"
        />
        <StatCard
          label="Avg Query Time"
          value="2.3ms"
          icon={Clock}
          color="bg-amber-500/15 text-amber-400"
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Recent Activity */}
        <div className="lg:col-span-2 rounded-xl border border-zinc-800 bg-zinc-900 p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-zinc-200">Recent Activity</h3>
            <RefreshCw size={14} className="text-zinc-500" />
          </div>
          <div className="space-y-3">
            {mockActivities.map((activity) => (
              <div
                key={activity.id}
                className="flex items-start gap-3 rounded-lg p-2 transition-colors hover:bg-zinc-800/50"
              >
                <div
                  className={`mt-0.5 rounded-md p-1.5 ${
                    activity.type === "instance"
                      ? "bg-green-500/15 text-green-400"
                      : activity.type === "mapping"
                      ? "bg-blue-500/15 text-blue-400"
                      : "bg-purple-500/15 text-purple-400"
                  }`}
                >
                  {activity.type === "instance" ? (
                    <Server size={14} />
                  ) : activity.type === "mapping" ? (
                    <Database size={14} />
                  ) : (
                    <Search size={14} />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-zinc-200">
                    {activity.action}
                  </p>
                  <p className="text-xs text-zinc-500 truncate">
                    {activity.detail}
                  </p>
                </div>
                <span className="shrink-0 text-xs text-zinc-600">
                  {activity.time}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-5">
          <h3 className="mb-4 text-sm font-semibold text-zinc-200">
            Quick Actions
          </h3>
          <div className="space-y-2">
            <Link
              href="/dashboard/mappings/new"
              className="flex items-center justify-between rounded-lg border border-zinc-800 p-3 text-sm text-zinc-300 transition-colors hover:border-blue-500/30 hover:bg-blue-500/5"
            >
              <div className="flex items-center gap-3">
                <Plus size={16} className="text-blue-400" />
                Create Mapping
              </div>
              <ArrowRight size={14} className="text-zinc-600" />
            </Link>
            <Link
              href="/dashboard/instances/new"
              className="flex items-center justify-between rounded-lg border border-zinc-800 p-3 text-sm text-zinc-300 transition-colors hover:border-green-500/30 hover:bg-green-500/5"
            >
              <div className="flex items-center gap-3">
                <Play size={16} className="text-green-400" />
                Launch Instance
              </div>
              <ArrowRight size={14} className="text-zinc-600" />
            </Link>
            <Link
              href="/dashboard/explorer"
              className="flex items-center justify-between rounded-lg border border-zinc-800 p-3 text-sm text-zinc-300 transition-colors hover:border-purple-500/30 hover:bg-purple-500/5"
            >
              <div className="flex items-center gap-3">
                <Compass size={16} className="text-purple-400" />
                Open Explorer
              </div>
              <ArrowRight size={14} className="text-zinc-600" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
