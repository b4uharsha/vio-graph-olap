import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Graph OLAP — Graph Analytics for Your Data Warehouse",
  description:
    "Turn your Snowflake, BigQuery, and Starburst data into in-memory graphs. Run multi-hop queries 120,000x faster than SQL. Zero idle cost. Open source under Apache 2.0.",
  keywords: [
    "graph analytics",
    "OLAP",
    "data warehouse",
    "Snowflake",
    "BigQuery",
    "Databricks",
    "Starburst",
    "graph database",
    "Cypher",
    "fraud detection",
    "supply chain",
    "PageRank",
    "open source",
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
