"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  Map,
  Server,
  Compass,
  Brain,
  Settings,
  Plus,
  ChevronLeft,
  ChevronRight,
  User,
} from "lucide-react";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/dashboard/mappings", label: "Mappings", icon: Map },
  { href: "/dashboard/instances", label: "Instances", icon: Server },
  { href: "/dashboard/explorer", label: "Explorer", icon: Compass },
  { href: "/dashboard/ai", label: "AI Assistant", icon: Brain },
  { href: "/dashboard/settings", label: "Settings", icon: Settings },
];

function getPageTitle(pathname: string): string {
  const item = navItems.find((n) =>
    pathname === n.href || (n.href !== "/dashboard" && pathname.startsWith(n.href + "/"))
  );
  if (pathname === "/dashboard") return "Dashboard";
  return item?.label ?? "Dashboard";
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [collapsed, setCollapsed] = useState(false);
  const pathname = usePathname();
  const pageTitle = getPageTitle(pathname);

  return (
    <div className="flex h-screen overflow-hidden bg-zinc-950">
      {/* Sidebar */}
      <aside
        className={`flex flex-col border-r border-zinc-800 bg-zinc-900 transition-all duration-300 ${
          collapsed ? "w-16" : "w-[220px]"
        }`}
      >
        {/* Logo */}
        <div className="flex h-14 items-center gap-2 border-b border-zinc-800 px-4">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-500/20 text-blue-400">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="3" />
              <circle cx="5" cy="6" r="2" />
              <circle cx="19" cy="6" r="2" />
              <circle cx="5" cy="18" r="2" />
              <circle cx="19" cy="18" r="2" />
              <line x1="7" y1="7" x2="10" y2="10" />
              <line x1="14" y1="10" x2="17" y2="7" />
              <line x1="7" y1="17" x2="10" y2="14" />
              <line x1="14" y1="14" x2="17" y2="17" />
            </svg>
          </div>
          {!collapsed && (
            <span className="text-sm font-semibold text-zinc-100">
              Graph OLAP
            </span>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 px-2 py-3">
          {navItems.map((item) => {
            const active =
              pathname === item.href ||
              (item.href !== "/dashboard" && pathname.startsWith(item.href + "/"));
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                  active
                    ? "bg-blue-500/15 text-blue-400"
                    : "text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"
                }`}
                title={collapsed ? item.label : undefined}
              >
                <Icon size={18} className="shrink-0" />
                {!collapsed && <span>{item.label}</span>}
              </Link>
            );
          })}
        </nav>

        {/* Collapse button */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex items-center justify-center border-t border-zinc-800 py-3 text-zinc-500 transition-colors hover:text-zinc-300"
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </aside>

      {/* Main content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top bar */}
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-zinc-800 bg-zinc-900/50 px-6">
          <h1 className="text-lg font-semibold text-zinc-100">{pageTitle}</h1>
          <div className="flex items-center gap-3">
            <Link
              href="/dashboard/instances/new"
              className="flex items-center gap-2 rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-blue-500"
            >
              <Plus size={14} />
              New Instance
            </Link>
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-zinc-700 text-zinc-300">
              <User size={16} />
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto p-6">
          <AnimatePresence mode="wait">
            <motion.div
              key={pathname}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.2 }}
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}
