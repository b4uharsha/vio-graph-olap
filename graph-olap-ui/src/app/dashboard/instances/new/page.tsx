"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowLeft, Database, Cpu, Clock, Server } from "lucide-react";
import { createInstance, listMappings } from "@/lib/api";
import type { Mapping } from "@/lib/mock-data";

const ttlOptions = [
  { value: 4, label: "4 hours" },
  { value: 8, label: "8 hours" },
  { value: 24, label: "24 hours" },
  { value: 48, label: "48 hours" },
];

export default function NewInstancePage() {
  const router = useRouter();
  const [mappings, setMappings] = useState<Mapping[]>([]);
  const [loadingMappings, setLoadingMappings] = useState(true);

  const [mappingId, setMappingId] = useState("");
  const [name, setName] = useState("");
  const [wrapperType, setWrapperType] = useState<"falkordb" | "ryugraph">("falkordb");
  const [ttl, setTtl] = useState(24);
  const [cpuCores, setCpuCores] = useState(4);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => {
    listMappings().then((data) => {
      setMappings(data);
      if (data.length > 0) setMappingId(data[0].id);
      setLoadingMappings(false);
    });
  }, []);

  function showToast(msg: string) {
    setToast(msg);
    setTimeout(() => setToast(null), 3000);
  }

  function validate(): boolean {
    const errs: Record<string, string> = {};
    if (!name.trim()) errs.name = "Instance name is required";
    if (!mappingId) errs.mapping = "Select a mapping";
    setErrors(errs);
    return Object.keys(errs).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;

    setSubmitting(true);
    try {
      await createInstance({
        name: name.trim(),
        mappingId,
        wrapperType,
        ttl,
        cpuCores,
      });
      showToast("Instance launched successfully");
      router.push("/dashboard/instances");
    } catch {
      showToast("Failed to create instance (API unavailable)");
      setSubmitting(false);
    }
  }

  const inputClass =
    "w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-200 placeholder-zinc-500 outline-none transition-colors focus:border-blue-500/50";

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      {/* Back link */}
      <button
        onClick={() => router.push("/dashboard/instances")}
        className="flex items-center gap-2 text-sm text-zinc-400 transition-colors hover:text-zinc-200"
      >
        <ArrowLeft size={14} />
        Back to Instances
      </button>

      <div>
        <h2 className="text-xl font-bold text-zinc-100">Launch Instance</h2>
        <p className="mt-1 text-sm text-zinc-400">
          Spin up a new graph database instance from a mapping
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Mapping selection */}
        <div className="space-y-4 rounded-xl border border-zinc-800 bg-zinc-900 p-5">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-zinc-300">
              Mapping <span className="text-red-400">*</span>
            </label>
            {loadingMappings ? (
              <div className="h-10 animate-pulse rounded-lg bg-zinc-800" />
            ) : (
              <select
                value={mappingId}
                onChange={(e) => setMappingId(e.target.value)}
                className={inputClass}
              >
                <option value="">Select a mapping</option>
                {mappings.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name} (v{m.version}) - {m.nodes.length} nodes, {m.edges.length} edges
                  </option>
                ))}
              </select>
            )}
            {errors.mapping && (
              <p className="mt-1 text-xs text-red-400">{errors.mapping}</p>
            )}
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-zinc-300">
              Instance Name <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. fraud-detection-prod"
              className={inputClass}
            />
            {errors.name && (
              <p className="mt-1 text-xs text-red-400">{errors.name}</p>
            )}
          </div>
        </div>

        {/* Wrapper Type */}
        <div className="space-y-3 rounded-xl border border-zinc-800 bg-zinc-900 p-5">
          <label className="block text-sm font-medium text-zinc-300">
            Wrapper Type
          </label>
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => setWrapperType("falkordb")}
              className={`rounded-lg border p-4 text-left transition-colors ${
                wrapperType === "falkordb"
                  ? "border-blue-500/50 bg-blue-500/10"
                  : "border-zinc-800 hover:border-zinc-700"
              }`}
            >
              <div className="flex items-center gap-2">
                <Database size={16} className={wrapperType === "falkordb" ? "text-blue-400" : "text-zinc-500"} />
                <span className={`text-sm font-medium ${wrapperType === "falkordb" ? "text-blue-300" : "text-zinc-300"}`}>
                  FalkorDB
                </span>
              </div>
              <p className="mt-2 text-xs text-zinc-500">
                Optimized for speed. Best for real-time queries, fraud detection, and low-latency lookups.
              </p>
            </button>
            <button
              type="button"
              onClick={() => setWrapperType("ryugraph")}
              className={`rounded-lg border p-4 text-left transition-colors ${
                wrapperType === "ryugraph"
                  ? "border-purple-500/50 bg-purple-500/10"
                  : "border-zinc-800 hover:border-zinc-700"
              }`}
            >
              <div className="flex items-center gap-2">
                <Server size={16} className={wrapperType === "ryugraph" ? "text-purple-400" : "text-zinc-500"} />
                <span className={`text-sm font-medium ${wrapperType === "ryugraph" ? "text-purple-300" : "text-zinc-300"}`}>
                  Ryugraph
                </span>
              </div>
              <p className="mt-2 text-xs text-zinc-500">
                Optimized for algorithms. Best for PageRank, community detection, and graph analytics.
              </p>
            </button>
          </div>
        </div>

        {/* TTL and CPU */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-3 rounded-xl border border-zinc-800 bg-zinc-900 p-5">
            <label className="flex items-center gap-2 text-sm font-medium text-zinc-300">
              <Clock size={14} className="text-zinc-500" />
              Time to Live
            </label>
            <select
              value={ttl}
              onChange={(e) => setTtl(Number(e.target.value))}
              className={inputClass}
            >
              {ttlOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-3 rounded-xl border border-zinc-800 bg-zinc-900 p-5">
            <label className="flex items-center gap-2 text-sm font-medium text-zinc-300">
              <Cpu size={14} className="text-zinc-500" />
              CPU Cores: {cpuCores}
            </label>
            <input
              type="range"
              min={1}
              max={8}
              value={cpuCores}
              onChange={(e) => setCpuCores(Number(e.target.value))}
              className="w-full accent-blue-500"
            />
            <div className="flex justify-between text-xs text-zinc-600">
              <span>1</span>
              <span>8</span>
            </div>
          </div>
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-lg bg-blue-600 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-500 disabled:opacity-50"
        >
          {submitting ? "Launching..." : "Launch Instance"}
        </button>
      </form>

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
