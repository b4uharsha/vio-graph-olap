"use client";

import {
  SigmaContainer,
  useLoadGraph,
  useRegisterEvents,
  useSigma,
  useCamera,
  useSetSettings,
} from "@react-sigma/core";
import "@react-sigma/core/lib/style.css";
import forceAtlas2 from "graphology-layout-forceatlas2";
import { useCallback, useEffect, useRef, useState } from "react";
import { createFraudGraph, type NodeAttributes } from "./graph-data";
import { NodePanel, type Neighbor } from "./node-panel";
import { Toolbar } from "./toolbar";

// -----------------------------------------------------------------------
// Inner component that runs inside SigmaContainer context
// -----------------------------------------------------------------------
function GraphEvents({
  onSelectNode,
}: {
  onSelectNode: (nodeId: string | null) => void;
}) {
  const sigma = useSigma();
  const registerEvents = useRegisterEvents();
  const setSettings = useSetSettings();

  const [hoveredNode, setHoveredNode] = useState<string | null>(null);

  // Register sigma events
  useEffect(() => {
    registerEvents({
      enterNode: (event) => setHoveredNode(event.node),
      leaveNode: () => setHoveredNode(null),
      clickNode: (event) => onSelectNode(event.node),
      clickStage: () => onSelectNode(null),
    });
  }, [registerEvents, onSelectNode]);

  // Highlight hovered node + neighbors, dim everything else
  useEffect(() => {
    if (hoveredNode) {
      const graph = sigma.getGraph();
      const neighbors = new Set(graph.neighbors(hoveredNode));
      neighbors.add(hoveredNode);

      const edgesOfHovered = new Set(graph.edges(hoveredNode));

      setSettings({
        nodeReducer: (node, data) => {
          const res = { ...data };
          if (!neighbors.has(node)) {
            res.color = "#27272a";
            res.label = "";
          }
          return res;
        },
        edgeReducer: (edge, data) => {
          const res = { ...data };
          if (!edgesOfHovered.has(edge)) {
            res.color = "rgba(39,39,42,0.3)";
          } else {
            res.color = "rgba(255,255,255,0.5)";
          }
          return res;
        },
      });
    } else {
      // Reset
      setSettings({
        nodeReducer: null,
        edgeReducer: null,
      });
    }
  }, [hoveredNode, sigma, setSettings]);

  return null;
}

// -----------------------------------------------------------------------
// Graph Loader — loads graph and runs ForceAtlas2 on mount
// -----------------------------------------------------------------------
function GraphLoader({
  onGraphLoaded,
  layoutRunning,
}: {
  onGraphLoaded: (nodeCount: number, edgeCount: number) => void;
  layoutRunning: boolean;
}) {
  const loadGraph = useLoadGraph();
  const sigma = useSigma();
  const animFrameRef = useRef<number>(0);
  const iterCountRef = useRef(0);

  // Load graph once
  useEffect(() => {
    const graph = createFraudGraph();
    loadGraph(graph);
    onGraphLoaded(graph.order, graph.size);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loadGraph]);

  // ForceAtlas2 animation loop
  useEffect(() => {
    if (!layoutRunning) {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      return;
    }

    const graph = sigma.getGraph();
    iterCountRef.current = 0;

    function step() {
      forceAtlas2.assign(graph, {
        iterations: 1,
        settings: {
          gravity: 1,
          scalingRatio: 10,
          slowDown: 1 + iterCountRef.current * 0.1,
          barnesHutOptimize: true,
        },
      });
      iterCountRef.current++;
      animFrameRef.current = requestAnimationFrame(step);
    }

    animFrameRef.current = requestAnimationFrame(step);

    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [layoutRunning, sigma]);

  return null;
}

// -----------------------------------------------------------------------
// Main exported component
// -----------------------------------------------------------------------
export interface GraphExplorerProps {
  className?: string;
}

export function GraphExplorer({ className = "" }: GraphExplorerProps) {
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [selectedAttrs, setSelectedAttrs] = useState<NodeAttributes | null>(null);
  const [neighbors, setNeighbors] = useState<Neighbor[]>([]);
  const [nodeCount, setNodeCount] = useState(0);
  const [edgeCount, setEdgeCount] = useState(0);
  const [layoutRunning, setLayoutRunning] = useState(true);
  const [fraudHighlighted, setFraudHighlighted] = useState(false);

  // We hold a ref to sigma via a callback to access graph outside SigmaContainer
  const sigmaRef = useRef<ReturnType<typeof useSigma> | null>(null);

  // Auto-stop layout after a few seconds
  useEffect(() => {
    if (!layoutRunning) return;
    const timer = setTimeout(() => setLayoutRunning(false), 3000);
    return () => clearTimeout(timer);
  }, [layoutRunning]);

  const handleSelectNode = useCallback((nodeId: string | null) => {
    if (!nodeId || !sigmaRef.current) {
      setSelectedNode(null);
      setSelectedAttrs(null);
      setNeighbors([]);
      return;
    }

    const graph = sigmaRef.current.getGraph();
    if (!graph.hasNode(nodeId)) return;

    const attrs = graph.getNodeAttributes(nodeId) as NodeAttributes;
    setSelectedNode(nodeId);
    setSelectedAttrs(attrs);

    // Build neighbor list
    const neighborList: Neighbor[] = [];
    graph.forEachEdge(nodeId, (edge, edgeAttrs, source, target) => {
      const otherId = source === nodeId ? target : source;
      const otherAttrs = graph.getNodeAttributes(otherId) as NodeAttributes;
      neighborList.push({
        id: otherId,
        label: otherAttrs.label,
        type: otherAttrs.nodeType,
        edgeLabel: edgeAttrs.label,
      });
    });
    setNeighbors(neighborList);
  }, []);

  const handleExpandNeighbors = useCallback(
    (nodeId: string) => {
      // In a real app this would fetch more data — for the demo, just zoom to the node
      if (!sigmaRef.current) return;
      const graph = sigmaRef.current.getGraph();
      const attrs = graph.getNodeAttributes(nodeId);
      sigmaRef.current.getCamera().animate(
        { x: attrs.x, y: attrs.y, ratio: 0.3 },
        { duration: 600 },
      );
    },
    [],
  );

  return (
    <div className={`relative w-full h-full overflow-hidden ${className}`}>
      {/* Mobile message */}
      <div className="md:hidden absolute inset-0 z-30 flex items-center justify-center bg-zinc-950/95 p-6 text-center">
        <div>
          <p className="text-lg font-semibold text-white mb-2">
            Graph Explorer works best on desktop
          </p>
          <p className="text-sm text-zinc-400">
            Resize your browser or open on a larger screen for the full
            interactive experience.
          </p>
        </div>
      </div>

      <SigmaContainer
        style={{ width: "100%", height: "100%", background: "#09090b" }}
        settings={{
          defaultNodeColor: "#3b82f6",
          defaultEdgeColor: "rgba(255,255,255,0.15)",
          labelColor: { color: "#a1a1aa" },
          labelFont: "Inter, system-ui, sans-serif",
          labelSize: 12,
          labelRenderedSizeThreshold: 8,
          renderEdgeLabels: false,
          enableEdgeEvents: false,
          zIndex: true,
        }}
        ref={(ref) => {
          // SigmaContainer ref gives us the sigma instance
          if (ref) {
            sigmaRef.current = {
              getGraph: () => ref.getGraph(),
              getCamera: () => ref.getCamera(),
            } as ReturnType<typeof useSigma>;
          }
        }}
      >
        <GraphLoader
          layoutRunning={layoutRunning}
          onGraphLoaded={(n, e) => {
            setNodeCount(n);
            setEdgeCount(e);
          }}
        />
        <GraphEvents onSelectNode={handleSelectNode} />
        <FraudHighlighter active={fraudHighlighted} />
        <CameraBridge />
      </SigmaContainer>

      <ToolbarWithCamera
        nodeCount={nodeCount}
        edgeCount={edgeCount}
        layoutRunning={layoutRunning}
        fraudHighlighted={fraudHighlighted}
        onToggleLayout={() => setLayoutRunning((v) => !v)}
        onToggleFraud={() => setFraudHighlighted((v) => !v)}
      />

      <NodePanel
        nodeId={selectedNode}
        attributes={selectedAttrs}
        neighbors={neighbors}
        onClose={() => {
          setSelectedNode(null);
          setSelectedAttrs(null);
          setNeighbors([]);
        }}
        onSelectNode={handleSelectNode}
        onExpandNeighbors={handleExpandNeighbors}
      />
    </div>
  );
}

// -----------------------------------------------------------------------
// Toolbar wrapper that uses the camera hook (must be inside SigmaContainer,
// but we want the Toolbar outside). We solve this by placing the toolbar
// outside and passing camera callbacks through a bridge component.
// -----------------------------------------------------------------------
// Actually, since the Toolbar is outside SigmaContainer, we cannot use
// useCamera inside it. We pass zoom/reset via the sigma ref instead.
function ToolbarWithCamera(props: {
  nodeCount: number;
  edgeCount: number;
  layoutRunning: boolean;
  fraudHighlighted: boolean;
  onToggleLayout: () => void;
  onToggleFraud: () => void;
}) {
  // We use a simple approach: read sigma ref from parent is not possible here
  // because we're outside the provider. Instead, dispatch custom events.
  return (
    <Toolbar
      {...props}
      onZoomIn={() => {
        document.dispatchEvent(new CustomEvent("graph-zoom", { detail: "in" }));
      }}
      onZoomOut={() => {
        document.dispatchEvent(new CustomEvent("graph-zoom", { detail: "out" }));
      }}
      onResetView={() => {
        document.dispatchEvent(new CustomEvent("graph-zoom", { detail: "reset" }));
      }}
    />
  );
}

// Bridge component inside SigmaContainer that listens to custom events
function CameraBridge() {
  const { zoomIn, zoomOut, reset } = useCamera();

  useEffect(() => {
    function handleZoom(e: Event) {
      const detail = (e as CustomEvent).detail;
      if (detail === "in") zoomIn();
      else if (detail === "out") zoomOut();
      else if (detail === "reset") reset();
    }
    document.addEventListener("graph-zoom", handleZoom);
    return () => document.removeEventListener("graph-zoom", handleZoom);
  }, [zoomIn, zoomOut, reset]);

  return null;
}

// Fraud highlighter — applies a node reducer when active
function FraudHighlighter({ active }: { active: boolean }) {
  const sigma = useSigma();
  const setSettings = useSetSettings();

  useEffect(() => {
    if (active) {
      const graph = sigma.getGraph();
      // Find all fraud-flagged nodes and their neighbors
      const fraudNodes = new Set<string>();
      graph.forEachNode((node, attrs) => {
        if ((attrs as NodeAttributes).flagged) {
          fraudNodes.add(node);
          graph.forEachNeighbor(node, (neighbor) => {
            fraudNodes.add(neighbor);
          });
        }
      });

      setSettings({
        nodeReducer: (node, data) => {
          const res = { ...data };
          const attrs = graph.getNodeAttributes(node) as NodeAttributes;
          if (attrs.flagged) {
            res.color = "#ef4444";
          } else if (fraudNodes.has(node)) {
            res.color = "#f97316";
          } else {
            res.color = "#27272a";
          }
          return res;
        },
        edgeReducer: (edge, data) => {
          const res = { ...data };
          const source = graph.source(edge);
          const target = graph.target(edge);
          if (fraudNodes.has(source) && fraudNodes.has(target)) {
            res.color = "rgba(239,68,68,0.5)";
          } else {
            res.color = "rgba(39,39,42,0.3)";
          }
          return res;
        },
      });
    } else {
      setSettings({
        nodeReducer: null,
        edgeReducer: null,
      });
    }
  }, [active, sigma, setSettings]);

  return null;
}
