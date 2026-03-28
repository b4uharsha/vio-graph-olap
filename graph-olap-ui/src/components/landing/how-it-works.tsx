"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { Table2, Rocket, Search } from "lucide-react";

const steps = [
  {
    icon: Table2,
    step: "01",
    title: "Define Mapping",
    description:
      "Choose tables from your warehouse, define which columns become nodes and which become edges. Visual mapper or YAML config.",
    visual: (
      <div className="mt-4 rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 font-mono text-xs leading-relaxed text-zinc-500">
        <div className="text-blue-400">nodes:</div>
        <div className="pl-4 text-zinc-400">
          - table: <span className="text-emerald-400">accounts</span>
        </div>
        <div className="pl-4 text-zinc-400">
          - table: <span className="text-emerald-400">transactions</span>
        </div>
        <div className="mt-1 text-blue-400">edges:</div>
        <div className="pl-4 text-zinc-400">
          - type: <span className="text-amber-400">TRANSFERRED_TO</span>
        </div>
      </div>
    ),
  },
  {
    icon: Rocket,
    step: "02",
    title: "Launch Instance",
    description:
      "One click to export data from your warehouse and spin up an isolated in-memory graph pod on Kubernetes.",
    visual: (
      <div className="mt-4 rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 font-mono text-xs leading-relaxed">
        <div className="text-zinc-500">$ graph-olap launch --mapping fraud.yaml</div>
        <div className="mt-1 text-blue-400">Exporting 2.4M rows from Snowflake...</div>
        <div className="text-emerald-400">Graph pod ready in 8.2s</div>
        <div className="text-emerald-400">Endpoint: graph-olap.internal:7687</div>
      </div>
    ),
  },
  {
    icon: Search,
    step: "03",
    title: "Query & Analyze",
    description:
      "Run Cypher queries and built-in graph algorithms. Results in milliseconds, not minutes.",
    visual: (
      <div className="mt-4 rounded-lg border border-zinc-800 bg-zinc-900/50 p-4 font-mono text-xs leading-relaxed">
        <div className="text-zinc-500">CALL algo.pageRank(&apos;Account&apos;)</div>
        <div className="mt-1 text-zinc-400">
          Computed in <span className="text-emerald-400">12ms</span> over{" "}
          <span className="text-blue-400">2.4M</span> nodes
        </div>
        <div className="text-amber-400">Top risk: ACC-4821 (score: 0.94)</div>
      </div>
    ),
  },
];

export function HowItWorks() {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <section
      id="how-it-works"
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
            From warehouse to graph in{" "}
            <span className="gradient-text">3 steps</span>
          </h2>
          <p className="mt-4 text-lg text-zinc-400">
            No ETL pipelines. No data duplication. Just point, map, and query.
          </p>
        </motion.div>

        <div className="mt-16 grid gap-8 md:grid-cols-3">
          {steps.map((step, i) => {
            const Icon = step.icon;
            return (
              <motion.div
                key={step.step}
                initial={{ opacity: 0, y: 30 }}
                animate={isInView ? { opacity: 1, y: 0 } : {}}
                transition={{ duration: 0.5, delay: 0.15 + i * 0.15 }}
                className="relative rounded-xl border border-zinc-800 bg-zinc-950 p-6"
              >
                {/* Step number */}
                <div className="mb-4 flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500/20 to-purple-500/20">
                    <Icon className="h-5 w-5 text-blue-400" />
                  </div>
                  <span className="font-mono text-sm text-zinc-600">{step.step}</span>
                </div>

                <h3 className="text-lg font-semibold">{step.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-zinc-400">
                  {step.description}
                </p>
                {step.visual}

                {/* Connector line (not on last) */}
                {i < steps.length - 1 && (
                  <div className="absolute top-1/2 -right-4 hidden h-px w-8 bg-gradient-to-r from-zinc-700 to-transparent md:block" />
                )}
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
