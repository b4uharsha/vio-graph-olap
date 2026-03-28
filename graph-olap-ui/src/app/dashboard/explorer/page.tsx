"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { motion } from "framer-motion";
import { Server } from "lucide-react";
import { listInstances } from "@/lib/api";
import type { Instance } from "@/lib/mock-data";

const GraphExplorer = dynamic(
  () => import("@/components/graph-explorer").then((mod) => mod.GraphExplorer),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-full items-center justify-center text-sm text-zinc-500">
        Loading graph explorer...
      </div>
    ),
  }
);

export default function ExplorerPage() {
  const [instances, setInstances] = useState<Instance[]>([]);
  const [selectedInstance, setSelectedInstance] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listInstances().then((data) => {
      const running = data.filter((i) => i.status === "running");
      setInstances(running);
      if (running.length > 0) setSelectedInstance(running[0].id);
      setLoading(false);
    });
  }, []);

  return (
    <div className="flex h-full flex-col gap-4">
      {/* Instance selector */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 text-sm text-zinc-400">
          <Server size={14} />
          <span>Instance:</span>
        </div>
        {loading ? (
          <div className="h-8 w-48 animate-pulse rounded-lg bg-zinc-800" />
        ) : instances.length > 0 ? (
          <select
            value={selectedInstance}
            onChange={(e) => setSelectedInstance(e.target.value)}
            className="rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-1.5 text-sm text-zinc-200 outline-none focus:border-blue-500/50"
          >
            {instances.map((inst) => (
              <option key={inst.id} value={inst.id}>
                {inst.name} ({inst.wrapperType})
              </option>
            ))}
          </select>
        ) : (
          <span className="text-sm text-zinc-500">
            No running instances available
          </span>
        )}
      </div>

      {/* Graph explorer */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex-1 overflow-hidden rounded-xl border border-zinc-800"
      >
        <GraphExplorer />
      </motion.div>
    </div>
  );
}
