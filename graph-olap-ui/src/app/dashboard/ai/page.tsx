"use client";

import { motion } from "framer-motion";
import { QueryAssistant } from "@/components/query-assistant";

export default function AIAssistantPage() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="mx-auto max-w-4xl"
    >
      <QueryAssistant />
    </motion.div>
  );
}
