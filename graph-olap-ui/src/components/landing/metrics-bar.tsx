"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { AnimatedCounter } from "@/components/ui/animated-counter";
import { Zap, DollarSign, Cable, Scale } from "lucide-react";

const metrics = [
  {
    icon: Zap,
    value: 120000,
    suffix: "x",
    label: "Faster",
    description: "Multi-hop query speed vs SQL",
  },
  {
    icon: DollarSign,
    value: 0,
    suffix: "",
    label: "Zero Idle Cost",
    description: "Pay nothing when nobody queries",
    customDisplay: "$0",
  },
  {
    icon: Cable,
    value: 50,
    suffix: "+",
    label: "Connectors",
    description: "Data warehouse integrations",
  },
  {
    icon: Scale,
    value: 2,
    suffix: ".0",
    label: "Apache License",
    description: "Fully open source",
    customDisplay: "Apache 2.0",
  },
];

export function MetricsBar() {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-50px" });

  return (
    <section ref={ref} className="relative border-y border-zinc-800/50 bg-zinc-950/50">
      <div className="mx-auto grid max-w-7xl grid-cols-2 gap-8 px-6 py-16 md:grid-cols-4 md:gap-0 md:divide-x md:divide-zinc-800/50">
        {metrics.map((metric, i) => {
          const Icon = metric.icon;
          return (
            <motion.div
              key={metric.label}
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.5, delay: i * 0.1 }}
              className="flex flex-col items-center text-center"
            >
              <Icon className="mb-3 h-5 w-5 text-blue-500" />
              <div className="text-3xl font-bold tracking-tight md:text-4xl">
                {metric.customDisplay ? (
                  <span>{metric.customDisplay}</span>
                ) : (
                  <AnimatedCounter target={metric.value} suffix={metric.suffix} />
                )}
              </div>
              <div className="mt-1 text-sm font-medium text-white">{metric.label}</div>
              <div className="mt-0.5 text-xs text-zinc-500">{metric.description}</div>
            </motion.div>
          );
        })}
      </div>
    </section>
  );
}
