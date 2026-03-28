"use client";

import {
  ZoomIn,
  ZoomOut,
  Maximize2,
  Play,
  Pause,
  AlertTriangle,
  CircleDot,
  GitBranch,
} from "lucide-react";

interface ToolbarProps {
  nodeCount: number;
  edgeCount: number;
  layoutRunning: boolean;
  fraudHighlighted: boolean;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onResetView: () => void;
  onToggleLayout: () => void;
  onToggleFraud: () => void;
}

export function Toolbar({
  nodeCount,
  edgeCount,
  layoutRunning,
  fraudHighlighted,
  onZoomIn,
  onZoomOut,
  onResetView,
  onToggleLayout,
  onToggleFraud,
}: ToolbarProps) {
  return (
    <div className="absolute top-4 left-4 right-4 md:left-4 md:right-auto z-10 flex flex-wrap items-center gap-2">
      {/* Zoom controls */}
      <div className="flex items-center gap-1 bg-zinc-900/80 backdrop-blur-md border border-zinc-700/60 rounded-lg px-1.5 py-1">
        <ToolbarButton icon={ZoomIn} tooltip="Zoom In" onClick={onZoomIn} />
        <ToolbarButton icon={ZoomOut} tooltip="Zoom Out" onClick={onZoomOut} />
        <ToolbarButton icon={Maximize2} tooltip="Reset View" onClick={onResetView} />
      </div>

      {/* Layout toggle */}
      <div className="bg-zinc-900/80 backdrop-blur-md border border-zinc-700/60 rounded-lg px-1.5 py-1">
        <ToolbarButton
          icon={layoutRunning ? Pause : Play}
          tooltip={layoutRunning ? "Stop Layout" : "Start Layout"}
          onClick={onToggleLayout}
          active={layoutRunning}
        />
      </div>

      {/* Fraud highlight */}
      <div className="bg-zinc-900/80 backdrop-blur-md border border-zinc-700/60 rounded-lg px-1.5 py-1">
        <ToolbarButton
          icon={AlertTriangle}
          tooltip={fraudHighlighted ? "Clear Fraud Highlight" : "Highlight Fraud"}
          onClick={onToggleFraud}
          active={fraudHighlighted}
          activeColor="text-red-400"
        />
      </div>

      {/* Stats */}
      <div className="flex items-center gap-3 bg-zinc-900/80 backdrop-blur-md border border-zinc-700/60 rounded-lg px-3 py-1.5 text-xs text-zinc-400">
        <span className="flex items-center gap-1.5">
          <CircleDot className="w-3 h-3" />
          {nodeCount} nodes
        </span>
        <span className="flex items-center gap-1.5">
          <GitBranch className="w-3 h-3" />
          {edgeCount} edges
        </span>
      </div>
    </div>
  );
}

function ToolbarButton({
  icon: Icon,
  tooltip,
  onClick,
  active = false,
  activeColor = "text-blue-400",
}: {
  icon: typeof ZoomIn;
  tooltip: string;
  onClick: () => void;
  active?: boolean;
  activeColor?: string;
}) {
  return (
    <button
      onClick={onClick}
      title={tooltip}
      className={`p-1.5 rounded-md transition-colors ${
        active
          ? `${activeColor} bg-white/10`
          : "text-zinc-400 hover:text-white hover:bg-white/10"
      }`}
    >
      <Icon className="w-4 h-4" />
    </button>
  );
}
