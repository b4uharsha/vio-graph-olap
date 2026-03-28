"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Settings, Database, Server } from "lucide-react";

export default function SettingsPage() {
  const [apiUrl, setApiUrl] = useState(
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8081"
  );

  const inputClass =
    "w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm text-zinc-200 placeholder-zinc-500 outline-none transition-colors focus:border-blue-500/50";

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h2 className="text-xl font-bold text-zinc-100">Settings</h2>
        <p className="mt-1 text-sm text-zinc-400">
          Configure your Graph OLAP environment
        </p>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-4 rounded-xl border border-zinc-800 bg-zinc-900 p-5"
      >
        <div className="flex items-center gap-2">
          <Server size={16} className="text-blue-400" />
          <h3 className="text-sm font-semibold text-zinc-200">API Configuration</h3>
        </div>
        <div>
          <label className="mb-1.5 block text-sm text-zinc-400">
            Backend API URL
          </label>
          <input
            type="text"
            value={apiUrl}
            onChange={(e) => setApiUrl(e.target.value)}
            className={inputClass}
          />
          <p className="mt-1.5 text-xs text-zinc-600">
            Set via NEXT_PUBLIC_API_URL environment variable
          </p>
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
        className="space-y-4 rounded-xl border border-zinc-800 bg-zinc-900 p-5"
      >
        <div className="flex items-center gap-2">
          <Database size={16} className="text-purple-400" />
          <h3 className="text-sm font-semibold text-zinc-200">Data Warehouse</h3>
        </div>
        <div className="space-y-3">
          <div>
            <label className="mb-1.5 block text-sm text-zinc-400">
              Connection Type
            </label>
            <select className={inputClass}>
              <option>Snowflake</option>
              <option>BigQuery</option>
              <option>Databricks</option>
              <option>Starburst</option>
            </select>
          </div>
          <div>
            <label className="mb-1.5 block text-sm text-zinc-400">
              Connection String
            </label>
            <input
              type="text"
              placeholder="snowflake://account.region.cloud/database"
              className={inputClass}
            />
          </div>
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="space-y-4 rounded-xl border border-zinc-800 bg-zinc-900 p-5"
      >
        <div className="flex items-center gap-2">
          <Settings size={16} className="text-amber-400" />
          <h3 className="text-sm font-semibold text-zinc-200">Preferences</h3>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-zinc-300">Auto-refresh instances</p>
            <p className="text-xs text-zinc-500">Poll running instances every 10 seconds</p>
          </div>
          <div className="h-5 w-9 rounded-full bg-blue-600 p-0.5">
            <div className="h-4 w-4 translate-x-4 rounded-full bg-white transition-transform" />
          </div>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-zinc-300">Mock data fallback</p>
            <p className="text-xs text-zinc-500">Show sample data when API is unavailable</p>
          </div>
          <div className="h-5 w-9 rounded-full bg-blue-600 p-0.5">
            <div className="h-4 w-4 translate-x-4 rounded-full bg-white transition-transform" />
          </div>
        </div>
      </motion.div>
    </div>
  );
}
