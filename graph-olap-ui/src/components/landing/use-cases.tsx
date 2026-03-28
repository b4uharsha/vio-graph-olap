"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { Shield, Pill, Truck, Lock } from "lucide-react";

const useCases = [
  {
    icon: Shield,
    title: "Fraud Detection",
    industry: "Banking",
    description:
      "Trace fraud rings through shared accounts, addresses, and beneficiaries in milliseconds. Detect circular transfers and shell company networks that SQL queries miss entirely.",
    color: "blue" as const,
  },
  {
    icon: Pill,
    title: "Drug Recall",
    industry: "Pharma",
    description:
      "Instantly map the cascade: which hospitals, distributors, and patients are affected by a contaminated batch. What used to take weeks now takes seconds.",
    color: "purple" as const,
  },
  {
    icon: Truck,
    title: "Supply Chain",
    industry: "Manufacturing",
    description:
      "When a supplier fails, see the full impact chain across your production lines. Identify alternate suppliers and predict delivery delays before they happen.",
    color: "emerald" as const,
  },
  {
    icon: Lock,
    title: "Access Analysis",
    industry: "IT Security",
    description:
      'Can this user reach the production database through any chain of permissions? Answer "who can access what" across your entire infrastructure in real time.',
    color: "amber" as const,
  },
];

const colorMap = {
  blue: {
    bg: "bg-blue-500/10",
    text: "text-blue-400",
    border: "hover:border-blue-500/30",
    shadow: "hover:shadow-blue-500/5",
    badge: "bg-blue-500/10 text-blue-400",
  },
  purple: {
    bg: "bg-purple-500/10",
    text: "text-purple-400",
    border: "hover:border-purple-500/30",
    shadow: "hover:shadow-purple-500/5",
    badge: "bg-purple-500/10 text-purple-400",
  },
  emerald: {
    bg: "bg-emerald-500/10",
    text: "text-emerald-400",
    border: "hover:border-emerald-500/30",
    shadow: "hover:shadow-emerald-500/5",
    badge: "bg-emerald-500/10 text-emerald-400",
  },
  amber: {
    bg: "bg-amber-500/10",
    text: "text-amber-400",
    border: "hover:border-amber-500/30",
    shadow: "hover:shadow-amber-500/5",
    badge: "bg-amber-500/10 text-amber-400",
  },
};

export function UseCases() {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <section id="use-cases" className="relative py-24 md:py-32" ref={ref}>
      <div className="mx-auto max-w-7xl px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
          className="mx-auto max-w-3xl text-center"
        >
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl md:text-5xl">
            Built for teams that{" "}
            <span className="gradient-text">need answers fast</span>
          </h2>
          <p className="mt-4 text-lg text-zinc-400">
            Graph OLAP powers critical workloads across industries where relationships matter.
          </p>
        </motion.div>

        <div className="mt-16 grid gap-6 sm:grid-cols-2">
          {useCases.map((uc, i) => {
            const Icon = uc.icon;
            const colors = colorMap[uc.color];
            return (
              <motion.div
                key={uc.title}
                initial={{ opacity: 0, y: 20 }}
                animate={isInView ? { opacity: 1, y: 0 } : {}}
                transition={{ duration: 0.5, delay: 0.1 + i * 0.1 }}
                className={`group relative overflow-hidden rounded-xl border border-zinc-800 bg-zinc-950 p-6 transition-all duration-300 hover:shadow-lg ${colors.border} ${colors.shadow}`}
              >
                <div className="flex items-start gap-4">
                  <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${colors.bg}`}>
                    <Icon className={`h-5 w-5 ${colors.text}`} />
                  </div>
                  <div>
                    <div className="flex items-center gap-3">
                      <h3 className="text-lg font-semibold">{uc.title}</h3>
                      <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${colors.badge}`}>
                        {uc.industry}
                      </span>
                    </div>
                    <p className="mt-2 text-sm leading-relaxed text-zinc-400">
                      {uc.description}
                    </p>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
