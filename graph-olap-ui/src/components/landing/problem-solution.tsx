"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";

const hops = [
  { hop: 1, sqlLines: 4, cypherLines: 1 },
  { hop: 2, sqlLines: 8, cypherLines: 1 },
  { hop: 3, sqlLines: 15, cypherLines: 1 },
  { hop: 4, sqlLines: 28, cypherLines: 1 },
  { hop: 5, sqlLines: 52, cypherLines: 1 },
  { hop: 6, sqlLines: 96, cypherLines: 2 },
];

export function ProblemSolution() {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <section id="problem" className="relative py-24 md:py-32" ref={ref}>
      <div className="mx-auto max-w-7xl px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
          className="mx-auto max-w-3xl text-center"
        >
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl md:text-5xl">
            Your Data Warehouse{" "}
            <span className="gradient-text">Can&apos;t Do This</span>
          </h2>
          <p className="mt-4 text-lg text-zinc-400">
            Multi-hop queries in SQL grow exponentially with each hop. In Cypher, they stay one line.
          </p>
        </motion.div>

        {/* Visual: SQL complexity growth vs Cypher */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="mx-auto mt-16 max-w-3xl"
        >
          <div className="overflow-hidden rounded-xl border border-zinc-800 bg-zinc-950 p-6 md:p-8">
            {/* Header */}
            <div className="mb-8 flex items-center justify-between text-sm">
              <span className="font-medium text-zinc-400">Lines of code per hop count</span>
              <div className="flex items-center gap-6">
                <span className="flex items-center gap-2">
                  <span className="h-3 w-3 rounded-sm bg-red-500/60" />
                  <span className="text-zinc-500">SQL</span>
                </span>
                <span className="flex items-center gap-2">
                  <span className="h-3 w-3 rounded-sm bg-emerald-500/60" />
                  <span className="text-zinc-500">Cypher</span>
                </span>
              </div>
            </div>

            {/* Bar chart */}
            <div className="space-y-4">
              {hops.map((row, i) => (
                <motion.div
                  key={row.hop}
                  initial={{ opacity: 0, x: -20 }}
                  animate={isInView ? { opacity: 1, x: 0 } : {}}
                  transition={{ duration: 0.4, delay: 0.3 + i * 0.08 }}
                  className="flex items-center gap-4"
                >
                  <span className="w-16 shrink-0 text-right text-sm text-zinc-500">
                    {row.hop} hop{row.hop > 1 ? "s" : ""}
                  </span>
                  <div className="flex flex-1 flex-col gap-1.5">
                    {/* SQL bar */}
                    <div className="flex items-center gap-2">
                      <div
                        className="h-5 rounded-sm bg-gradient-to-r from-red-500/40 to-red-500/60 transition-all duration-700"
                        style={{ width: `${Math.min((row.sqlLines / 96) * 100, 100)}%` }}
                      />
                      <span className="shrink-0 text-xs font-mono text-red-400">
                        {row.sqlLines} lines
                      </span>
                    </div>
                    {/* Cypher bar */}
                    <div className="flex items-center gap-2">
                      <div
                        className="h-5 rounded-sm bg-gradient-to-r from-emerald-500/40 to-emerald-500/60"
                        style={{ width: `${(row.cypherLines / 96) * 100}%`, minWidth: "8px" }}
                      />
                      <span className="shrink-0 text-xs font-mono text-emerald-400">
                        {row.cypherLines} line{row.cypherLines > 1 ? "s" : ""}
                      </span>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>

            {/* Bottom message */}
            <div className="mt-8 rounded-lg border border-zinc-800 bg-zinc-900/50 px-4 py-3 text-center text-sm text-zinc-400">
              At 6 hops, SQL requires <span className="font-semibold text-red-400">96 lines</span>{" "}
              with exponential JOINs. Cypher stays at{" "}
              <span className="font-semibold text-emerald-400">2 lines</span>.
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
