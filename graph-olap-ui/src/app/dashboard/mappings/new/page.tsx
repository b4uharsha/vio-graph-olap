"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Plus, Trash2, ArrowLeft, Database } from "lucide-react";
import { createMapping } from "@/lib/api";
import type { NodeDefinition, EdgeDefinition } from "@/lib/mock-data";

const emptyNode: NodeDefinition = { label: "", sql: "", primaryKey: "" };
const emptyEdge: EdgeDefinition = { type: "", sql: "", fromColumn: "", toColumn: "" };

export default function NewMappingPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [nodes, setNodes] = useState<NodeDefinition[]>([{ ...emptyNode }]);
  const [edges, setEdges] = useState<EdgeDefinition[]>([{ ...emptyEdge }]);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  function validate(): boolean {
    const errs: Record<string, string> = {};
    if (!name.trim()) errs.name = "Name is required";
    const validNodes = nodes.filter((n) => n.label.trim());
    if (validNodes.length === 0) errs.nodes = "At least one node is required";
    setErrors(errs);
    return Object.keys(errs).length === 0;
  }

  function showToast(msg: string) {
    setToast(msg);
    setTimeout(() => setToast(null), 3000);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;

    setSubmitting(true);
    try {
      await createMapping({
        name: name.trim(),
        description: description.trim(),
        nodes: nodes.filter((n) => n.label.trim()),
        edges: edges.filter((e) => e.type.trim()),
      });
      showToast("Mapping created successfully");
      router.push("/dashboard/mappings");
    } catch {
      showToast("Failed to create mapping (API unavailable)");
      setSubmitting(false);
    }
  }

  function updateNode(idx: number, field: keyof NodeDefinition, value: string) {
    setNodes((prev) =>
      prev.map((n, i) => (i === idx ? { ...n, [field]: value } : n))
    );
  }

  function updateEdge(idx: number, field: keyof EdgeDefinition, value: string) {
    setEdges((prev) =>
      prev.map((e, i) => (i === idx ? { ...e, [field]: value } : e))
    );
  }

  function removeNode(idx: number) {
    setNodes((prev) => prev.filter((_, i) => i !== idx));
  }

  function removeEdge(idx: number) {
    setEdges((prev) => prev.filter((_, i) => i !== idx));
  }

  const inputClass =
    "w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-200 placeholder-zinc-500 outline-none transition-colors focus:border-blue-500/50";

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* Back link */}
      <button
        onClick={() => router.push("/dashboard/mappings")}
        className="flex items-center gap-2 text-sm text-zinc-400 transition-colors hover:text-zinc-200"
      >
        <ArrowLeft size={14} />
        Back to Mappings
      </button>

      <div>
        <h2 className="text-xl font-bold text-zinc-100">Create Mapping</h2>
        <p className="mt-1 text-sm text-zinc-400">
          Define how your SQL tables map to graph nodes and edges
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Info */}
        <div className="space-y-4 rounded-xl border border-zinc-800 bg-zinc-900 p-5">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-zinc-300">
              Name <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Customer Graph"
              className={inputClass}
            />
            {errors.name && (
              <p className="mt-1 text-xs text-red-400">{errors.name}</p>
            )}
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-zinc-300">
              Description
            </label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional description"
              className={inputClass}
            />
          </div>
        </div>

        {/* Node Definitions */}
        <div className="space-y-4 rounded-xl border border-zinc-800 bg-zinc-900 p-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Database size={16} className="text-blue-400" />
              <h3 className="text-sm font-semibold text-zinc-200">
                Node Definitions
              </h3>
            </div>
            <button
              type="button"
              onClick={() => setNodes((prev) => [...prev, { ...emptyNode }])}
              className="flex items-center gap-1.5 rounded-md bg-zinc-800 px-2.5 py-1 text-xs text-zinc-300 transition-colors hover:bg-zinc-700"
            >
              <Plus size={12} />
              Add Node
            </button>
          </div>
          {errors.nodes && (
            <p className="text-xs text-red-400">{errors.nodes}</p>
          )}
          <div className="space-y-3">
            {nodes.map((node, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                className="grid grid-cols-[1fr_2fr_1fr_auto] gap-3 rounded-lg border border-zinc-800/50 bg-zinc-950/50 p-3"
              >
                <input
                  type="text"
                  value={node.label}
                  onChange={(e) => updateNode(idx, "label", e.target.value)}
                  placeholder="Label"
                  className={inputClass}
                />
                <input
                  type="text"
                  value={node.sql}
                  onChange={(e) => updateNode(idx, "sql", e.target.value)}
                  placeholder="SQL query"
                  className={`${inputClass} font-mono`}
                />
                <input
                  type="text"
                  value={node.primaryKey}
                  onChange={(e) => updateNode(idx, "primaryKey", e.target.value)}
                  placeholder="Primary key"
                  className={inputClass}
                />
                <button
                  type="button"
                  onClick={() => removeNode(idx)}
                  disabled={nodes.length === 1}
                  className="self-center rounded-md p-1.5 text-zinc-600 transition-colors hover:bg-red-500/10 hover:text-red-400 disabled:opacity-30 disabled:hover:bg-transparent disabled:hover:text-zinc-600"
                >
                  <Trash2 size={14} />
                </button>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Edge Definitions */}
        <div className="space-y-4 rounded-xl border border-zinc-800 bg-zinc-900 p-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ArrowLeft size={16} className="rotate-180 text-purple-400" />
              <h3 className="text-sm font-semibold text-zinc-200">
                Edge Definitions
              </h3>
            </div>
            <button
              type="button"
              onClick={() => setEdges((prev) => [...prev, { ...emptyEdge }])}
              className="flex items-center gap-1.5 rounded-md bg-zinc-800 px-2.5 py-1 text-xs text-zinc-300 transition-colors hover:bg-zinc-700"
            >
              <Plus size={12} />
              Add Edge
            </button>
          </div>
          <div className="space-y-3">
            {edges.map((edge, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                className="grid grid-cols-[1fr_2fr_1fr_1fr_auto] gap-3 rounded-lg border border-zinc-800/50 bg-zinc-950/50 p-3"
              >
                <input
                  type="text"
                  value={edge.type}
                  onChange={(e) => updateEdge(idx, "type", e.target.value)}
                  placeholder="Type"
                  className={inputClass}
                />
                <input
                  type="text"
                  value={edge.sql}
                  onChange={(e) => updateEdge(idx, "sql", e.target.value)}
                  placeholder="SQL query"
                  className={`${inputClass} font-mono`}
                />
                <input
                  type="text"
                  value={edge.fromColumn}
                  onChange={(e) => updateEdge(idx, "fromColumn", e.target.value)}
                  placeholder="From col"
                  className={inputClass}
                />
                <input
                  type="text"
                  value={edge.toColumn}
                  onChange={(e) => updateEdge(idx, "toColumn", e.target.value)}
                  placeholder="To col"
                  className={inputClass}
                />
                <button
                  type="button"
                  onClick={() => removeEdge(idx)}
                  disabled={edges.length === 1}
                  className="self-center rounded-md p-1.5 text-zinc-600 transition-colors hover:bg-red-500/10 hover:text-red-400 disabled:opacity-30 disabled:hover:bg-transparent disabled:hover:text-zinc-600"
                >
                  <Trash2 size={14} />
                </button>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-lg bg-blue-600 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-500 disabled:opacity-50"
        >
          {submitting ? "Creating..." : "Create Mapping"}
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
