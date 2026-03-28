import { GithubIcon } from "@/components/ui/github-icon";

const footerLinks = {
  Product: [
    { label: "Features", href: "#features" },
    { label: "How It Works", href: "#how-it-works" },
    { label: "Use Cases", href: "#use-cases" },
    { label: "Pricing", href: "#pricing" },
  ],
  Developers: [
    { label: "Documentation", href: "#" },
    { label: "API Reference", href: "#" },
    { label: "GitHub", href: "https://github.com/graph-olap" },
    { label: "Changelog", href: "#" },
  ],
  Company: [
    { label: "About", href: "#" },
    { label: "Blog", href: "#" },
    { label: "Contact", href: "#" },
    { label: "Careers", href: "#" },
  ],
};

export function Footer() {
  return (
    <footer className="border-t border-zinc-800/50 bg-zinc-950">
      <div className="mx-auto max-w-7xl px-6 py-16">
        <div className="grid gap-12 md:grid-cols-2 lg:grid-cols-5">
          {/* Brand column */}
          <div className="lg:col-span-2">
            <a href="#" className="flex items-center gap-2 text-lg font-semibold tracking-tight">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-purple-600">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <circle cx="4" cy="4" r="2" fill="white" />
                  <circle cx="12" cy="4" r="2" fill="white" />
                  <circle cx="8" cy="12" r="2" fill="white" />
                  <line x1="4" y1="4" x2="12" y2="4" stroke="white" strokeWidth="1.5" />
                  <line x1="4" y1="4" x2="8" y2="12" stroke="white" strokeWidth="1.5" />
                  <line x1="12" y1="4" x2="8" y2="12" stroke="white" strokeWidth="1.5" />
                </svg>
              </div>
              <span>Graph OLAP</span>
            </a>
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-zinc-500">
              Turn your data warehouse into a graph analytics powerhouse. Open source, warehouse-native, blazing fast.
            </p>
            <div className="mt-6 flex items-center gap-4">
              <a
                href="https://github.com/graph-olap"
                target="_blank"
                rel="noopener noreferrer"
                className="text-zinc-500 transition-colors hover:text-white"
              >
                <GithubIcon className="h-5 w-5" />
              </a>
              <span className="rounded-full border border-zinc-800 px-3 py-1 text-xs text-zinc-500">
                Apache 2.0
              </span>
            </div>
          </div>

          {/* Link columns */}
          {Object.entries(footerLinks).map(([title, links]) => (
            <div key={title}>
              <h4 className="text-sm font-semibold text-zinc-300">{title}</h4>
              <ul className="mt-4 space-y-3">
                {links.map((link) => (
                  <li key={link.label}>
                    <a
                      href={link.href}
                      className="text-sm text-zinc-500 transition-colors hover:text-zinc-300"
                    >
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div className="mt-16 flex flex-col items-center justify-between gap-4 border-t border-zinc-800/50 pt-8 md:flex-row">
          <p className="text-sm text-zinc-600">
            Built by Harsha Reddy
          </p>
          <p className="text-sm text-zinc-600">
            &copy; {new Date().getFullYear()} Graph OLAP. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
