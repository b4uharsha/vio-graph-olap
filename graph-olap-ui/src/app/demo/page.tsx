"use client";

import dynamic from "next/dynamic";

const GraphExplorer = dynamic(
  () =>
    import("@/components/graph-explorer/graph-explorer").then(
      (mod) => mod.GraphExplorer,
    ),
  {
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center h-screen bg-[#09090b]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-zinc-500">Loading Graph Explorer...</p>
        </div>
      </div>
    ),
  },
);

export default function DemoPage() {
  return (
    <main className="h-screen w-screen bg-[#09090b]">
      <GraphExplorer className="h-full w-full" />
    </main>
  );
}
