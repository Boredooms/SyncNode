import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { MagneticButton } from "@/components/MagneticButton";

export default function NotFound() {
  return (
    <section className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden px-6 text-center">
      {/* Animated connection line */}
      <svg
        aria-hidden="true"
        className="pointer-events-none absolute inset-x-0 top-1/2 h-px w-full"
        style={{ opacity: 0.5 }}
      >
        <line
          x1="0"
          y1="0.5"
          x2="100%"
          y2="0.5"
          stroke="#222222"
          strokeWidth="1"
          strokeDasharray="6 8"
          className="animate-[dashmove_1.6s_linear_infinite]"
        />
      </svg>
      <style>{`@keyframes dashmove { to { stroke-dashoffset: -28; } }`}</style>

      <div className="relative z-10">
        <div className="font-mono text-micro uppercase tracking-wider2 text-fg-faint">
          404
        </div>
        <h1 className="mt-6 text-[clamp(2.4rem,7vw,5rem)] font-extralight tracking-tight text-fg-primary">
          NODE NOT FOUND
        </h1>
        <p className="mx-auto mt-5 max-w-md text-[14px] leading-relaxed text-fg-mute">
          The route you requested does not exist in this workspace. It may have
          been moved, or it may never have been built.
        </p>
        <div className="mt-10">
          <MagneticButton to="/" variant="secondary" size="lg">
            <ArrowLeft className="h-4 w-4" />
            RETURN HOME
          </MagneticButton>
        </div>
      </div>
    </section>
  );
}
