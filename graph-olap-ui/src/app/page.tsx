import { Navbar } from "@/components/landing/navbar";
import { Hero } from "@/components/landing/hero";
import { MetricsBar } from "@/components/landing/metrics-bar";
import { ProblemSolution } from "@/components/landing/problem-solution";
import { FeaturesGrid } from "@/components/landing/features-grid";
import { HowItWorks } from "@/components/landing/how-it-works";
import { UseCases } from "@/components/landing/use-cases";
import { ComparisonTable } from "@/components/landing/comparison-table";
import { CtaSection } from "@/components/landing/cta-section";
import { Footer } from "@/components/landing/footer";

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen bg-background font-sans">
      <Navbar />
      <main className="flex-1">
        <Hero />
        <MetricsBar />
        <ProblemSolution />
        <FeaturesGrid />
        <HowItWorks />
        <UseCases />
        <ComparisonTable />
        <CtaSection />
      </main>
      <Footer />
    </div>
  );
}
