"use client";

import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Sparkles, Copy, Play, Check, Loader2 } from "lucide-react";
import { CypherHighlight } from "./cypher-highlight";

const EXAMPLE_QUERIES = [
  "Show all fraud-flagged customers",
  "Find customers connected to fraud within 3 hops",
  "Which accounts have the highest transfer volume?",
  "Find shared addresses between flagged customers",
  "Run PageRank on the customer network",
];

interface QueryResult {
  cypher: string;
  explanation: string;
  isDemo?: boolean;
}

type QueryState = "empty" | "loading" | "result" | "error";

export function QueryAssistant() {
  const [question, setQuestion] = useState("");
  const [state, setState] = useState<QueryState>("empty");
  const [result, setResult] = useState<QueryResult | null>(null);
  const [error, setError] = useState<string>("");
  const [copied, setCopied] = useState(false);
  const [toastVisible, setToastVisible] = useState(false);

  const handleSubmit = useCallback(
    async (q?: string) => {
      const query = q || question;
      if (!query.trim()) return;

      if (q) setQuestion(q);
      setState("loading");
      setError("");
      setResult(null);

      try {
        const res = await fetch("/api/cypher", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question: query }),
        });

        if (!res.ok) {
          const data = await res.json();
          throw new Error(data.error || `Request failed (${res.status})`);
        }

        const data: QueryResult = await res.json();
        setResult(data);
        setState("result");
      } catch (err) {
        setError(err instanceof Error ? err.message : "Something went wrong");
        setState("error");
      }
    },
    [question]
  );

  const handleCopy = useCallback(async () => {
    if (!result) return;
    await navigator.clipboard.writeText(result.cypher);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [result]);

  const handleRun = useCallback(() => {
    setToastVisible(true);
    setTimeout(() => setToastVisible(false), 3000);
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto">
      {/* Search input */}
      <div className="relative">
        <div className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500">
          <Search className="h-5 w-5" />
        </div>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about your graph..."
          className="w-full rounded-2xl border border-zinc-700/50 bg-zinc-900/80 py-4 pl-12 pr-24 text-base text-zinc-100 placeholder-zinc-500 outline-none backdrop-blur-sm transition-all focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20"
        />
        <button
          onClick={() => handleSubmit()}
          disabled={!question.trim() || state === "loading"}
          className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 px-4 py-2 text-sm font-medium text-white transition-all hover:from-blue-500 hover:to-purple-500 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <Sparkles className="h-4 w-4" />
          Generate
        </button>
      </div>

      {/* Example chips */}
      <AnimatePresence mode="wait">
        {state === "empty" && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className="mt-4 flex flex-wrap gap-2"
          >
            {EXAMPLE_QUERIES.map((eq) => (
              <button
                key={eq}
                onClick={() => handleSubmit(eq)}
                className="rounded-full border border-zinc-800 bg-zinc-900/50 px-3 py-1.5 text-xs text-zinc-400 transition-all hover:border-purple-500/50 hover:bg-purple-500/10 hover:text-purple-300"
              >
                {eq}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Loading state */}
      <AnimatePresence mode="wait">
        {state === "loading" && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3 }}
            className="mt-8 flex flex-col items-center gap-3"
          >
            <Loader2 className="h-8 w-8 animate-spin text-purple-500" />
            <p className="text-sm text-zinc-500">Generating Cypher query...</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error state */}
      <AnimatePresence mode="wait">
        {state === "error" && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3 }}
            className="mt-8 rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400"
          >
            {error}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Result state */}
      <AnimatePresence mode="wait">
        {state === "result" && result && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3 }}
            className="mt-8 space-y-4"
          >
            {/* Demo badge */}
            {result.isDemo && (
              <div className="inline-flex items-center gap-1.5 rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-xs text-amber-400">
                <Sparkles className="h-3 w-3" />
                Demo mode — set ANTHROPIC_API_KEY for live AI generation
              </div>
            )}

            {/* Code block */}
            <div className="relative overflow-hidden rounded-xl border border-zinc-800 shadow-2xl shadow-blue-500/5">
              {/* Header */}
              <div className="flex items-center justify-between border-b border-zinc-800 bg-zinc-950 px-4 py-2">
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full bg-red-500/70" />
                  <div className="h-3 w-3 rounded-full bg-yellow-500/70" />
                  <div className="h-3 w-3 rounded-full bg-green-500/70" />
                  <span className="ml-2 text-xs text-zinc-600">
                    generated.cypher
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleCopy}
                    className="flex items-center gap-1 rounded-md px-2 py-1 text-xs text-zinc-500 transition-colors hover:bg-zinc-800 hover:text-zinc-300"
                  >
                    {copied ? (
                      <>
                        <Check className="h-3.5 w-3.5 text-green-500" />
                        Copied
                      </>
                    ) : (
                      <>
                        <Copy className="h-3.5 w-3.5" />
                        Copy Query
                      </>
                    )}
                  </button>
                  <button
                    onClick={handleRun}
                    className="flex items-center gap-1 rounded-md bg-blue-600/20 px-2 py-1 text-xs text-blue-400 transition-colors hover:bg-blue-600/30"
                  >
                    <Play className="h-3.5 w-3.5" />
                    Run Query
                  </button>
                </div>
              </div>

              {/* Highlighted code */}
              <CypherHighlight code={result.cypher} className="rounded-none border-0" />
            </div>

            {/* Explanation */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="rounded-lg border border-zinc-800/50 bg-zinc-900/50 p-4"
            >
              <p className="mb-1 text-xs font-medium uppercase tracking-wider text-purple-400">
                Explanation
              </p>
              <p className="text-sm leading-relaxed text-zinc-400">
                {result.explanation}
              </p>
            </motion.div>

            {/* Try another */}
            <div className="flex flex-wrap gap-2 pt-2">
              <span className="text-xs text-zinc-600 self-center mr-1">Try another:</span>
              {EXAMPLE_QUERIES.filter((eq) => eq !== question).slice(0, 3).map((eq) => (
                <button
                  key={eq}
                  onClick={() => handleSubmit(eq)}
                  className="rounded-full border border-zinc-800 bg-zinc-900/50 px-3 py-1.5 text-xs text-zinc-400 transition-all hover:border-purple-500/50 hover:bg-purple-500/10 hover:text-purple-300"
                >
                  {eq}
                </button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Toast notification */}
      <AnimatePresence>
        {toastVisible && (
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 50 }}
            className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 rounded-lg border border-zinc-700 bg-zinc-800 px-4 py-3 text-sm text-zinc-300 shadow-xl"
          >
            Connect to a Graph OLAP instance to run queries
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
