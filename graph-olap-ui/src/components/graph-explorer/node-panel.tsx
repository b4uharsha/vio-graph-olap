"use client";

import { motion, AnimatePresence } from "framer-motion";
import { X, User, Landmark, MapPin, Phone, ChevronRight } from "lucide-react";
import type { NodeAttributes } from "./graph-data";

const TYPE_ICONS: Record<string, typeof User> = {
  Customer: User,
  Account: Landmark,
  Address: MapPin,
  Phone: Phone,
};

const TYPE_COLORS: Record<string, string> = {
  Customer: "text-blue-400",
  Account: "text-green-400",
  Address: "text-orange-400",
  Phone: "text-purple-400",
};

export interface Neighbor {
  id: string;
  label: string;
  type: string;
  edgeLabel: string;
}

interface NodePanelProps {
  nodeId: string | null;
  attributes: NodeAttributes | null;
  neighbors: Neighbor[];
  onClose: () => void;
  onSelectNode: (id: string) => void;
  onExpandNeighbors: (id: string) => void;
}

export function NodePanel({
  nodeId,
  attributes,
  neighbors,
  onClose,
  onSelectNode,
  onExpandNeighbors,
}: NodePanelProps) {
  const isOpen = nodeId !== null && attributes !== null;
  const Icon = attributes ? TYPE_ICONS[attributes.type] || User : User;
  const colorClass = attributes ? TYPE_COLORS[attributes.type] || "text-white" : "text-white";

  return (
    <AnimatePresence>
      {isOpen && attributes && nodeId && (
        <motion.div
          key="node-panel"
          initial={{ x: "100%" }}
          animate={{ x: 0 }}
          exit={{ x: "100%" }}
          transition={{ type: "spring", damping: 25, stiffness: 300 }}
          className="absolute right-0 top-0 bottom-0 w-80 bg-zinc-800/95 backdrop-blur-md border-l border-zinc-700 z-20 overflow-y-auto"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-zinc-700">
            <div className="flex items-center gap-2">
              <Icon className={`w-5 h-5 ${colorClass}`} />
              <span className="text-xs font-medium uppercase tracking-wider text-zinc-400">
                {attributes.type}
              </span>
            </div>
            <button
              onClick={onClose}
              className="p-1 rounded hover:bg-zinc-700 transition-colors"
            >
              <X className="w-4 h-4 text-zinc-400" />
            </button>
          </div>

          {/* Node label */}
          <div className="px-4 pt-4 pb-2">
            <h3 className="text-lg font-semibold text-white">{attributes.label}</h3>
            <p className="text-xs text-zinc-500 font-mono mt-1">ID: {nodeId}</p>
          </div>

          {/* Flagged badge */}
          {attributes.flagged && (
            <div className="mx-4 mb-3 px-3 py-1.5 rounded bg-red-500/15 border border-red-500/30 text-red-400 text-xs font-medium flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
              Flagged for Fraud
            </div>
          )}

          {/* Properties */}
          <div className="px-4 pb-4">
            <h4 className="text-xs font-medium uppercase tracking-wider text-zinc-500 mb-2">
              Properties
            </h4>
            <div className="space-y-1.5">
              {attributes.balance !== undefined && (
                <Property label="Balance" value={`$${attributes.balance.toLocaleString()}`} />
              )}
              {attributes.since && <Property label="Since" value={attributes.since} />}
              {attributes.street && <Property label="Street" value={attributes.street} />}
              {attributes.city && <Property label="City" value={attributes.city} />}
              {attributes.number && <Property label="Number" value={attributes.number} />}
              <Property label="Connections" value={String(neighbors.length)} />
            </div>
          </div>

          {/* Expand button */}
          <div className="px-4 pb-3">
            <button
              onClick={() => onExpandNeighbors(nodeId)}
              className="w-full py-2 px-3 rounded-md bg-blue-500/15 border border-blue-500/30 text-blue-400 text-sm font-medium hover:bg-blue-500/25 transition-colors"
            >
              Expand Neighbors ({neighbors.length})
            </button>
          </div>

          {/* Neighbors list */}
          <div className="px-4 pb-6">
            <h4 className="text-xs font-medium uppercase tracking-wider text-zinc-500 mb-2">
              Connected Nodes
            </h4>
            <div className="space-y-1">
              {neighbors.map((n, i) => {
                const NIcon = TYPE_ICONS[n.type] || User;
                const nColor = TYPE_COLORS[n.type] || "text-white";
                return (
                  <button
                    key={`${n.id}-${n.edgeLabel}-${i}`}
                    onClick={() => onSelectNode(n.id)}
                    className="w-full flex items-center gap-2 px-2 py-1.5 rounded hover:bg-zinc-700/60 transition-colors text-left group"
                  >
                    <NIcon className={`w-3.5 h-3.5 ${nColor} shrink-0`} />
                    <div className="min-w-0 flex-1">
                      <span className="text-sm text-zinc-200 truncate block">
                        {n.label}
                      </span>
                      <span className="text-[10px] text-zinc-500 font-mono">
                        {n.edgeLabel}
                      </span>
                    </div>
                    <ChevronRight className="w-3.5 h-3.5 text-zinc-600 group-hover:text-zinc-400 shrink-0" />
                  </button>
                );
              })}
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function Property({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between text-sm">
      <span className="text-zinc-500">{label}</span>
      <span className="text-zinc-200 font-mono text-xs">{value}</span>
    </div>
  );
}
