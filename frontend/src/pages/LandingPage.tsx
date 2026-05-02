import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { ArrowRight, ArrowDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import PipelineTimeline from "@/components/PipelineTimeline";
import FeatureGrid from "@/components/FeatureGrid";
import { api } from "@/lib/api";

export default function LandingPage() {
  const [count, setCount] = useState<number | null>(null);

  useEffect(() => {
    api
      .listPlates(1000, 0)
      .then((r) => setCount(r.plates.length))
      .catch(() => setCount(null));
  }, []);

  function scrollToPipeline() {
    document.getElementById("pipeline")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1">
        {/* HERO */}
        <section className="container pt-20 md:pt-32 pb-16 md:pb-24">
          <div className="max-w-3xl">
            <p className="font-mono text-xs uppercase tracking-[0.18em] text-primary mb-5">
              PlateScan · License Plate Recognition · Digital Image Processing
            </p>
            <h1 className="text-4xl md:text-6xl font-semibold tracking-tight leading-[1.05]">
              Read any license plate from a single photo.
            </h1>
            <p className="mt-6 text-lg text-muted-foreground max-w-2xl leading-relaxed">
              A classical computer vision pipeline that locates a license plate in a vehicle image and
              reads its characters — built with OpenCV and Tesseract.
            </p>

            <div className="mt-8 flex flex-col sm:flex-row gap-3">
              <Button asChild size="lg" className="gap-2">
                <Link to="/demo">
                  Try Live Demo <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
              <Button variant="outline" size="lg" onClick={scrollToPipeline} className="gap-2">
                See the Pipeline <ArrowDown className="h-4 w-4" />
              </Button>
            </div>

            <div className="mt-10 flex items-center gap-2 font-mono text-xs text-muted-foreground">
              <span className="h-1.5 w-1.5 rounded-full bg-primary" />
              {count === null
                ? "Connecting to backend…"
                : `${count} plate${count === 1 ? "" : "s"} recognized so far`}
            </div>
          </div>
        </section>

        <PipelineTimeline />
        <FeatureGrid />
      </main>

      <Footer />
    </div>
  );
}
