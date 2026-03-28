"use client";

import React from "react";

const KEYWORDS = [
  "MATCH",
  "WHERE",
  "RETURN",
  "WITH",
  "ORDER BY",
  "LIMIT",
  "CREATE",
  "DELETE",
  "SET",
  "REMOVE",
  "MERGE",
  "OPTIONAL",
  "UNWIND",
  "CALL",
  "YIELD",
  "DISTINCT",
  "AS",
  "AND",
  "OR",
  "NOT",
  "IN",
  "IS",
  "NULL",
  "TRUE",
  "FALSE",
  "COUNT",
  "SUM",
  "AVG",
  "MIN",
  "MAX",
  "COLLECT",
  "BY",
  "ASC",
  "DESC",
];

interface Token {
  type: "keyword" | "node" | "rel" | "string" | "number" | "comment" | "property" | "text";
  value: string;
}

function tokenize(code: string): Token[] {
  const tokens: Token[] = [];
  let i = 0;

  while (i < code.length) {
    // Comments
    if (code[i] === "/" && code[i + 1] === "/") {
      let end = code.indexOf("\n", i);
      if (end === -1) end = code.length;
      tokens.push({ type: "comment", value: code.slice(i, end) });
      i = end;
      continue;
    }

    // Strings (single or double quotes)
    if (code[i] === "'" || code[i] === '"') {
      const quote = code[i];
      let j = i + 1;
      while (j < code.length && code[j] !== quote) {
        if (code[j] === "\\") j++;
        j++;
      }
      tokens.push({ type: "string", value: code.slice(i, j + 1) });
      i = j + 1;
      continue;
    }

    // Node patterns: (variable:Label ...) or (:Label)
    if (code[i] === "(") {
      let depth = 1;
      let j = i + 1;
      while (j < code.length && depth > 0) {
        if (code[j] === "(") depth++;
        if (code[j] === ")") depth--;
        j++;
      }
      const inner = code.slice(i, j);
      if (inner.includes(":")) {
        tokens.push({ type: "node", value: inner });
      } else {
        tokens.push({ type: "text", value: inner });
      }
      i = j;
      continue;
    }

    // Relationship patterns: -[...]-> or <-[...]-  or -[...]-
    if (
      (code[i] === "-" && code[i + 1] === "[") ||
      (code[i] === "<" && code[i + 1] === "-" && code[i + 2] === "[")
    ) {
      const start = i;
      let j = code.indexOf("]", i);
      if (j !== -1) {
        j++;
        // consume trailing -> or -
        while (j < code.length && (code[j] === "-" || code[j] === ">")) j++;
        tokens.push({ type: "rel", value: code.slice(start, j) });
        i = j;
        continue;
      }
    }

    // Arrow shorthand: --> or <-- without brackets
    if (code[i] === "-" && code[i + 1] === "-" && code[i + 2] === ">") {
      tokens.push({ type: "rel", value: "-->" });
      i += 3;
      continue;
    }
    if (code[i] === "<" && code[i + 1] === "-" && code[i + 2] === "-") {
      tokens.push({ type: "rel", value: "<--" });
      i += 3;
      continue;
    }

    // Numbers
    if (/[0-9]/.test(code[i]) && (i === 0 || /[\s,({[\-+*/><=]/.test(code[i - 1]))) {
      let j = i;
      while (j < code.length && /[0-9.]/.test(code[j])) j++;
      tokens.push({ type: "number", value: code.slice(i, j) });
      i = j;
      continue;
    }

    // $parameters
    if (code[i] === "$") {
      let j = i + 1;
      while (j < code.length && /[a-zA-Z0-9_]/.test(code[j])) j++;
      tokens.push({ type: "property", value: code.slice(i, j) });
      i = j;
      continue;
    }

    // Words (check for keywords)
    if (/[a-zA-Z_]/.test(code[i])) {
      let j = i;
      while (j < code.length && /[a-zA-Z0-9_.]/.test(code[j])) j++;
      const word = code.slice(i, j);

      // Check for multi-word keywords like ORDER BY
      let fullWord = word;
      if (word === "ORDER" || word === "GROUP") {
        const rest = code.slice(j);
        const byMatch = rest.match(/^\s+BY/);
        if (byMatch) {
          fullWord = word + byMatch[0];
          j += byMatch[0].length;
        }
      }

      if (KEYWORDS.includes(fullWord.toUpperCase())) {
        tokens.push({ type: "keyword", value: fullWord });
      } else if (word.includes(".")) {
        tokens.push({ type: "property", value: word });
      } else {
        tokens.push({ type: "text", value: word });
      }
      i = j;
      continue;
    }

    // Whitespace and other characters
    tokens.push({ type: "text", value: code[i] });
    i++;
  }

  return tokens;
}

const colorMap: Record<Token["type"], string> = {
  keyword: "text-blue-400 font-semibold",
  node: "text-emerald-400",
  rel: "text-amber-400",
  string: "text-orange-300",
  number: "text-purple-400",
  comment: "text-zinc-600 italic",
  property: "text-cyan-400",
  text: "text-zinc-300",
};

interface CypherHighlightProps {
  code: string;
  className?: string;
}

export function CypherHighlight({ code, className = "" }: CypherHighlightProps) {
  const tokens = tokenize(code);

  return (
    <div
      className={`overflow-x-auto rounded-lg bg-zinc-900 p-4 font-mono text-sm leading-relaxed ${className}`}
      style={{ fontFamily: "var(--font-geist-mono), monospace" }}
    >
      <pre className="whitespace-pre-wrap">
        <code>
          {tokens.map((token, i) => (
            <span key={i} className={colorMap[token.type]}>
              {token.value}
            </span>
          ))}
        </code>
      </pre>
    </div>
  );
}
