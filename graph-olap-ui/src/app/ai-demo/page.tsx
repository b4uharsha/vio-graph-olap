"use client";

import { motion } from "framer-motion";
import { MessageSquare, Cpu, Play, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { QueryAssistant } from "@/components/query-assistant";

const steps = [
  {
    icon: MessageSquare,
    title: "Ask",
    description: "Type your question in plain English. No Cypher knowledge needed.",
    color: "text-blue-400",
    bg: "bg-blue-500/10",
    border: "border-blue-500/20",
  },
  {
    icon: Cpu,
    title: "Generate",
    description: "AI translates your question into an optimized Cypher query instantly.",
    color: "text-purple-400",
    bg: "bg-purple-500/10",
    border: "border-purple-500/20",
  },
  {
    icon: Play,
    title: "Run",
    description: "Execute against your Graph OLAP instance and explore results visually.",
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/20",
  },
];

export default function AIDemoPage() {
  return (
    <div className="min-h-screen bg-zinc-950">
      {/* Background */}
      <div className="grid-bg fixed inset-0 pointer-events-none" />
      <div className="pointer-events-none fixed top-0 left-1/3 h-[600px] w-[600px] rounded-full bg-purple-500/5 blur-3xl" />
      <div className="pointer-events-none fixed bottom-0 right-1/3 h-[600px] w-[600px] rounded-full bg-blue-500/5 blur-3xl" />

      <div className="relative mx-auto max-w-5xl px-6 py-12">
        {/* Back link */}
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-sm text-zinc-500 transition-colors hover:text-zinc-300 mb-12"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to home
        </Link>

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center mb-12"
        >
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-purple-500/30 bg-purple-500/10 px-4 py-1.5 text-sm text-purple-400">
            <Cpu className="h-4 w-4" />
            AI-Powered
          </div>
          <h1 className="text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
            <span className="gradient-text">AI-Powered</span> Graph Queries
          </h1>
          <p className="mt-4 text-lg text-zinc-400 max-w-2xl mx-auto">
            Ask questions in English. Get Cypher queries instantly.
          </p>
        </motion.div>

        {/* Query Assistant */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <QueryAssistant />
        </motion.div>

        {/* How it works */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="mt-24"
        >
          <h2 className="text-center text-2xl font-bold mb-2">How it works</h2>
          <p className="text-center text-zinc-500 mb-10">
            From natural language to graph queries in seconds
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {steps.map((step, i) => (
              <motion.div
                key={step.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.5 + i * 0.1 }}
                className={`relative rounded-xl border ${step.border} ${step.bg} p-6`}
              >
                {/* Step number */}
                <div className="absolute -top-3 -left-3 flex h-7 w-7 items-center justify-center rounded-full bg-zinc-950 border border-zinc-700 text-xs font-bold text-zinc-400">
                  {i + 1}
                </div>

                <step.icon className={`h-8 w-8 ${step.color} mb-4`} />
                <h3 className="text-lg font-semibold text-zinc-100 mb-2">
                  {step.title}
                </h3>
                <p className="text-sm text-zinc-400 leading-relaxed">
                  {step.description}
                </p>

                {/* Connector arrow (not on last) */}
                {i < steps.length - 1 && (
                  <div className="hidden md:block absolute top-1/2 -right-3 -translate-y-1/2 text-zinc-700">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                      <path
                        d="M5 12h14m0 0l-6-6m6 6l-6 6"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Schema info */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.8 }}
          className="mt-16 rounded-xl border border-zinc-800/50 bg-zinc-900/30 p-6 text-center"
        >
          <p className="text-sm text-zinc-500">
            Demo schema includes{" "}
            <span className="text-zinc-300">Customer</span>,{" "}
            <span className="text-zinc-300">Account</span>,{" "}
            <span className="text-zinc-300">Address</span>, and{" "}
            <span className="text-zinc-300">Phone</span> nodes with{" "}
            <span className="text-zinc-300">OWNS_ACCOUNT</span>,{" "}
            <span className="text-zinc-300">LIVES_AT</span>,{" "}
            <span className="text-zinc-300">HAS_PHONE</span>, and{" "}
            <span className="text-zinc-300">TRANSFERS_TO</span> relationships.
          </p>
        </motion.div>
      </div>
    </div>
  );
}
