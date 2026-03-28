"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { Check, X, Minus } from "lucide-react";

type CellValue = "yes" | "no" | "partial" | string;

interface ComparisonRow {
  feature: string;
  graphOlap: CellValue;
  neo4j: CellValue;
  puppyGraph: CellValue;
  neptune: CellValue;
}

const rows: ComparisonRow[] = [
  {
    feature: "Warehouse-native",
    graphOlap: "yes",
    neo4j: "no",
    puppyGraph: "yes",
    neptune: "no",
  },
  {
    feature: "Multi-hop speed",
    graphOlap: "120,000x vs SQL",
    neo4j: "Fast",
    puppyGraph: "Slow (virtualized)",
    neptune: "Moderate",
  },
  {
    feature: "Zero idle cost",
    graphOlap: "yes",
    neo4j: "no",
    puppyGraph: "no",
    neptune: "partial",
  },
  {
    feature: "Per-analyst isolation",
    graphOlap: "yes",
    neo4j: "no",
    puppyGraph: "no",
    neptune: "no",
  },
  {
    feature: "Built-in algorithms",
    graphOlap: "yes",
    neo4j: "yes",
    puppyGraph: "no",
    neptune: "partial",
  },
  {
    feature: "Open source",
    graphOlap: "Apache 2.0",
    neo4j: "AGPL / Commercial",
    puppyGraph: "no",
    neptune: "no",
  },
  {
    feature: "K8s-native deploy",
    graphOlap: "yes",
    neo4j: "partial",
    puppyGraph: "no",
    neptune: "no",
  },
  {
    feature: "Self-hosted option",
    graphOlap: "yes",
    neo4j: "yes",
    puppyGraph: "no",
    neptune: "no",
  },
];

function CellDisplay({ value }: { value: CellValue }) {
  if (value === "yes") {
    return (
      <span className="flex items-center justify-center">
        <Check className="h-5 w-5 text-emerald-400" />
      </span>
    );
  }
  if (value === "no") {
    return (
      <span className="flex items-center justify-center">
        <X className="h-5 w-5 text-zinc-600" />
      </span>
    );
  }
  if (value === "partial") {
    return (
      <span className="flex items-center justify-center">
        <Minus className="h-5 w-5 text-amber-400" />
      </span>
    );
  }
  return <span className="text-sm text-zinc-400">{value}</span>;
}

export function ComparisonTable() {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <section
      id="pricing"
      className="relative border-y border-zinc-800/50 bg-zinc-950/50 py-24 md:py-32"
      ref={ref}
    >
      <div className="mx-auto max-w-7xl px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
          className="mx-auto max-w-3xl text-center"
        >
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl md:text-5xl">
            Why <span className="gradient-text">Graph OLAP</span>?
          </h2>
          <p className="mt-4 text-lg text-zinc-400">
            See how Graph OLAP compares to other graph solutions.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="mt-16 overflow-x-auto"
        >
          <table className="w-full min-w-[640px] border-collapse">
            <thead>
              <tr className="border-b border-zinc-800">
                <th className="px-4 py-4 text-left text-sm font-medium text-zinc-500">
                  Feature
                </th>
                <th className="px-4 py-4 text-center text-sm font-semibold text-blue-400">
                  Graph OLAP
                </th>
                <th className="px-4 py-4 text-center text-sm font-medium text-zinc-500">
                  Neo4j
                </th>
                <th className="px-4 py-4 text-center text-sm font-medium text-zinc-500">
                  PuppyGraph
                </th>
                <th className="px-4 py-4 text-center text-sm font-medium text-zinc-500">
                  AWS Neptune
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => (
                <tr
                  key={row.feature}
                  className={`border-b border-zinc-800/50 ${
                    i % 2 === 0 ? "bg-zinc-950/50" : ""
                  }`}
                >
                  <td className="px-4 py-3.5 text-sm font-medium text-zinc-300">
                    {row.feature}
                  </td>
                  <td className="px-4 py-3.5 text-center">
                    <CellDisplay value={row.graphOlap} />
                  </td>
                  <td className="px-4 py-3.5 text-center">
                    <CellDisplay value={row.neo4j} />
                  </td>
                  <td className="px-4 py-3.5 text-center">
                    <CellDisplay value={row.puppyGraph} />
                  </td>
                  <td className="px-4 py-3.5 text-center">
                    <CellDisplay value={row.neptune} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </motion.div>
      </div>
    </section>
  );
}
