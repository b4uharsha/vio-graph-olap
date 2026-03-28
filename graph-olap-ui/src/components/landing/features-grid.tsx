"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import {
  Zap,
  Shield,
  BarChart3,
  Database,
  Server,
  Globe,
} from "lucide-react";

const features = [
  {
    icon: Zap,
    title: "Zero Idle Cost",
    description:
      "Instances auto-terminate when idle. Pay nothing when nobody is querying. Scales back up in seconds.",
  },
  {
    icon: Shield,
    title: "Per-Analyst Isolation",
    description:
      "Each analyst gets their own private graph instance. No noisy neighbors, no shared state, full data isolation.",
  },
  {
    icon: BarChart3,
    title: "Built-in Algorithms",
    description:
      "PageRank, betweenness centrality, community detection, shortest path, and 20+ graph algorithms out of the box.",
  },
  {
    icon: Database,
    title: "Warehouse Native",
    description:
      "First-class connectors for Snowflake, BigQuery, Starburst, and Databricks. Your data stays where it is.",
  },
  {
    icon: Server,
    title: "K8s Native",
    description:
      "Helm charts, auto-scaling with KEDA, pod-per-user architecture. Deploy on any Kubernetes cluster.",
  },
  {
    icon: Globe,
    title: "Open Source",
    description:
      "Apache 2.0 licensed. No vendor lock-in, no phone-home telemetry. Deploy in your VPC, your network, your rules.",
  },
];

export function FeaturesGrid() {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <section id="features" className="relative py-24 md:py-32" ref={ref}>
      <div className="mx-auto max-w-7xl px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
          className="mx-auto max-w-3xl text-center"
        >
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl md:text-5xl">
            Everything you need for{" "}
            <span className="gradient-text">graph analytics</span>
          </h2>
          <p className="mt-4 text-lg text-zinc-400">
            Production-grade graph infrastructure that connects to your existing data stack.
          </p>
        </motion.div>

        <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature, i) => {
            const Icon = feature.icon;
            return (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                animate={isInView ? { opacity: 1, y: 0 } : {}}
                transition={{ duration: 0.5, delay: 0.1 + i * 0.08 }}
                className="group relative overflow-hidden rounded-xl border border-zinc-800 bg-zinc-950 p-6 transition-all duration-300 hover:border-blue-500/30 hover:shadow-lg hover:shadow-blue-500/5"
              >
                {/* Subtle glow on hover */}
                <div className="pointer-events-none absolute inset-0 bg-gradient-to-br from-blue-500/5 to-purple-500/5 opacity-0 transition-opacity duration-300 group-hover:opacity-100" />

                <div className="relative">
                  <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-blue-500/10">
                    <Icon className="h-5 w-5 text-blue-400" />
                  </div>
                  <h3 className="text-lg font-semibold">{feature.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-zinc-400">
                    {feature.description}
                  </p>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
