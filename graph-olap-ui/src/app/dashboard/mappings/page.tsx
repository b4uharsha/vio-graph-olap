"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Plus,
  Search,
  Eye,
  Pencil,
  Trash2,
  Database,
} from "lucide-react";
import { listMappings, deleteMapping } from "@/lib/api";
import type { Mapping } from "@/lib/mock-data";

export default function MappingsPage() {
  const [mappings, setMappings] = useState<Mapping[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => {
    listMappings().then((data) => {
      setMappings(data);
      setLoading(false);
    });
  }, []);

  const filtered = useMemo(
    () =>
      mappings.filter((m) =>
        m.name.toLowerCase().includes(search.toLowerCase())
      ),
    [mappings, search]
  );

  function showToast(msg: string) {
    setToast(msg);
    setTimeout(() => setToast(null), 3000);
  }

  async function handleDelete(id: string, name: string) {
    if (!confirm(`Delete mapping "${name}"?`)) return;
    try {
      await deleteMapping(id);
      setMappings((prev) => prev.filter((m) => m.id !== id));
      showToast(`Mapping "${name}" deleted`);
    } catch {
      showToast("Failed to delete mapping (API unavailable)");
    }
  }

  function formatDate(iso: string) {
    return new Date(iso).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-zinc-100">Mappings</h2>
          <p className="mt-1 text-sm text-zinc-400">
            Define how SQL tables map to graph nodes and edges
          </p>
        </div>
        <Link
          href="/dashboard/mappings/new"
          className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-500"
        >
          <Plus size={16} />
          Create Mapping
        </Link>
      </div>

      {/* Search */}
      <div className="relative">
        <Search
          size={16}
          className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500"
        />
        <input
          type="text"
          placeholder="Search mappings..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-lg border border-zinc-800 bg-zinc-900 py-2 pl-9 pr-4 text-sm text-zinc-200 placeholder-zinc-500 outline-none transition-colors focus:border-blue-500/50"
        />
      </div>

      {/* Loading skeleton */}
      {loading && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-16 animate-pulse rounded-lg border border-zinc-800 bg-zinc-900"
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
          <Database size={40} className="text-zinc-600" />
          <p className="mt-4 text-zinc-400">
            {search
              ? "No mappings match your search."
              : "No mappings yet. Create your first mapping to get started."}
          </p>
          {!search && (
            <Link
              href="/dashboard/mappings/new"
              className="mt-4 flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500"
            >
              <Plus size={14} />
              Create Mapping
            </Link>
          )}
        </motion.div>
      )}

      {/* Table */}
      {!loading && filtered.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-zinc-800">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-zinc-800 bg-zinc-900/80 text-left">
                <th className="px-4 py-3 font-medium text-zinc-400">Name</th>
                <th className="px-4 py-3 font-medium text-zinc-400">Owner</th>
                <th className="px-4 py-3 font-medium text-zinc-400">Version</th>
                <th className="px-4 py-3 font-medium text-zinc-400">Nodes</th>
                <th className="px-4 py-3 font-medium text-zinc-400">Edges</th>
                <th className="px-4 py-3 font-medium text-zinc-400">Created</th>
                <th className="px-4 py-3 font-medium text-zinc-400 text-right">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((mapping, idx) => (
                <motion.tr
                  key={mapping.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: idx * 0.05 }}
                  className="border-b border-zinc-800/50 transition-colors hover:bg-zinc-900/50"
                >
                  <td className="px-4 py-3">
                    <div>
                      <p className="font-medium text-zinc-200">
                        {mapping.name}
                      </p>
                      {mapping.description && (
                        <p className="text-xs text-zinc-500 truncate max-w-[200px]">
                          {mapping.description}
                        </p>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-zinc-400">{mapping.owner}</td>
                  <td className="px-4 py-3">
                    <span className="rounded-full bg-zinc-800 px-2 py-0.5 text-xs text-zinc-300">
                      v{mapping.version}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-zinc-400">
                    {mapping.nodes.length}
                  </td>
                  <td className="px-4 py-3 text-zinc-400">
                    {mapping.edges.length}
                  </td>
                  <td className="px-4 py-3 text-zinc-400">
                    {formatDate(mapping.createdAt)}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        title="View"
                        className="rounded-md p-1.5 text-zinc-500 transition-colors hover:bg-zinc-800 hover:text-zinc-300"
                      >
                        <Eye size={15} />
                      </button>
                      <button
                        title="Edit"
                        className="rounded-md p-1.5 text-zinc-500 transition-colors hover:bg-zinc-800 hover:text-zinc-300"
                      >
                        <Pencil size={15} />
                      </button>
                      <button
                        title="Delete"
                        onClick={() => handleDelete(mapping.id, mapping.name)}
                        className="rounded-md p-1.5 text-zinc-500 transition-colors hover:bg-red-500/10 hover:text-red-400"
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Toast */}
      {toast && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0 }}
          className="fixed bottom-6 right-6 rounded-lg border border-zinc-700 bg-zinc-800 px-4 py-3 text-sm text-zinc-200 shadow-xl"
        >
          {toast}
        </motion.div>
      )}
    </div>
  );
}
