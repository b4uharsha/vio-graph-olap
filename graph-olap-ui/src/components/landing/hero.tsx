"use client";

import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import { GithubIcon } from "@/components/ui/github-icon";
import { useState } from "react";

const sqlCode = `-- Find fraud chains: accounts sharing
-- addresses with flagged beneficiaries
SELECT DISTINCT a3.account_id
FROM accounts a1
JOIN addresses addr1
  ON a1.address_id = addr1.id
JOIN accounts a2
  ON a2.address_id = addr1.id
JOIN transfers t
  ON t.from_account = a2.account_id
JOIN beneficiaries b
  ON b.id = t.beneficiary_id
JOIN accounts a3
  ON a3.beneficiary_id = b.id
WHERE a1.flagged = true
  AND t.amount > 10000;`;

const cypherCode = `// Same query in Cypher — 2 lines
MATCH (a:Account {flagged: true})-[:SHARES_ADDRESS]->()<-[:SHARES_ADDRESS]-(b:Account)
      -[:TRANSFERRED_TO]->(c:Beneficiary)<-[:LINKED_TO]-(d:Account)
WHERE a.amount > 10000
RETURN DISTINCT d.account_id`;

export function Hero() {
  const [activeTab, setActiveTab] = useState<"sql" | "cypher">("sql");

  return (
    <section className="relative overflow-hidden pt-32 pb-20 md:pt-40 md:pb-32">
      {/* Background grid */}
      <div className="grid-bg absolute inset-0" />

      {/* Glow orbs */}
      <div className="pointer-events-none absolute top-20 left-1/4 h-96 w-96 rounded-full bg-blue-500/10 blur-3xl" />
      <div className="pointer-events-none absolute top-40 right-1/4 h-96 w-96 rounded-full bg-purple-500/10 blur-3xl" />

      <div className="relative mx-auto max-w-7xl px-6">
        <div className="mx-auto max-w-4xl text-center">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="mb-8 inline-flex items-center gap-2 rounded-full border border-zinc-800 bg-zinc-900/50 px-4 py-1.5 text-sm text-zinc-400"
          >
            <span className="h-2 w-2 rounded-full bg-green-500" />
            Open Source &mdash; Apache 2.0
          </motion.div>

          {/* Headline */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-4xl font-bold leading-tight tracking-tight sm:text-5xl md:text-6xl lg:text-7xl"
          >
            <span className="gradient-text">Graph Analytics</span> on Your{" "}
            <br className="hidden sm:block" />
            Data Warehouse
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-zinc-400 md:text-xl"
          >
            Turn your Snowflake, BigQuery, and Starburst data into in-memory graphs.
            Run multi-hop queries{" "}
            <span className="font-semibold text-white">120,000x faster</span> than SQL.
            Zero idle cost.
          </motion.p>

          {/* CTAs */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center"
          >
            <a
              href="#get-started"
              className="group flex items-center gap-2 rounded-lg bg-blue-600 px-6 py-3 text-sm font-medium text-white transition-all hover:bg-blue-500 hover:shadow-lg hover:shadow-blue-500/25"
            >
              Try Free Demo
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </a>
            <a
              href="https://github.com/graph-olap"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 rounded-lg border border-zinc-700 px-6 py-3 text-sm font-medium text-zinc-300 transition-all hover:border-zinc-500 hover:text-white"
            >
              <GithubIcon className="h-4 w-4" />
              View on GitHub
            </a>
          </motion.div>
        </div>

        {/* Code comparison */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.5 }}
          className="mx-auto mt-16 max-w-3xl"
        >
          <div className="overflow-hidden rounded-xl border border-zinc-800 bg-zinc-950 shadow-2xl shadow-blue-500/5">
            {/* Tab bar */}
            <div className="flex border-b border-zinc-800">
              <button
                onClick={() => setActiveTab("sql")}
                className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
                  activeTab === "sql"
                    ? "bg-zinc-900 text-red-400"
                    : "text-zinc-500 hover:text-zinc-300"
                }`}
              >
                SQL &mdash; 15 lines, 6 JOINs
              </button>
              <button
                onClick={() => setActiveTab("cypher")}
                className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
                  activeTab === "cypher"
                    ? "bg-zinc-900 text-green-400"
                    : "text-zinc-500 hover:text-zinc-300"
                }`}
              >
                Cypher &mdash; 4 lines, 0 JOINs
              </button>
            </div>

            {/* Code area */}
            <div className="relative p-6">
              <pre className="overflow-x-auto font-mono text-sm leading-relaxed">
                <code className={activeTab === "sql" ? "text-zinc-400" : "text-emerald-400"}>
                  {activeTab === "sql" ? sqlCode : cypherCode}
                </code>
              </pre>
              {activeTab === "sql" && (
                <div className="absolute right-6 bottom-6 rounded-md bg-red-500/10 px-3 py-1 text-xs font-medium text-red-400">
                  Slow &amp; complex
                </div>
              )}
              {activeTab === "cypher" && (
                <div className="absolute right-6 bottom-6 rounded-md bg-green-500/10 px-3 py-1 text-xs font-medium text-green-400">
                  120,000x faster
                </div>
              )}
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
