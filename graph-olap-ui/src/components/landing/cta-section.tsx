"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { ArrowRight } from "lucide-react";

export function CtaSection() {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <section id="get-started" className="relative py-24 md:py-32" ref={ref}>
      {/* Background glow */}
      <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
        <div className="h-64 w-64 rounded-full bg-blue-500/10 blur-3xl" />
        <div className="absolute h-64 w-64 rounded-full bg-purple-500/10 blur-3xl" />
      </div>

      <div className="relative mx-auto max-w-7xl px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
          className="mx-auto max-w-2xl text-center"
        >
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl md:text-5xl">
            Ready to unlock{" "}
            <span className="gradient-text">graph intelligence</span>?
          </h2>
          <p className="mt-4 text-lg text-zinc-400">
            Start exploring your warehouse data as a graph in minutes. Free tier available,
            no credit card required.
          </p>

          <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            <a
              href="#"
              className="group flex items-center gap-2 rounded-lg bg-blue-600 px-8 py-3.5 text-sm font-medium text-white transition-all hover:bg-blue-500 hover:shadow-lg hover:shadow-blue-500/25"
            >
              Get Started Free
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </a>
            <a
              href="#"
              className="text-sm font-medium text-zinc-400 transition-colors hover:text-white"
            >
              Schedule a Demo &rarr;
            </a>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
