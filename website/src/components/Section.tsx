import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { Reveal } from "@/animations/Reveal";
import { SplitText } from "@/animations/SplitText";

/** Eyebrow label with leading rule — encodes the section's chapter. */
export function SectionLabel({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("mb-6 flex items-center gap-3", className)}>
      <span className="h-px w-8 bg-line" aria-hidden="true" />
      <span className="eyebrow">{children}</span>
    </div>
  );
}

/** Large editorial section heading with fall-in animation. */
export function SectionHeading({
  children,
  className,
  as = "h2",
  animate = true,
}: {
  children: string;
  className?: string;
  as?: "h1" | "h2" | "h3";
  animate?: boolean;
}) {
  const Tag = as;
  if (!animate) {
    return <Tag className={className}>{children}</Tag>;
  }
  return (
    <SplitText as={as} mode="rise" className={className}>
      {children}
    </SplitText>
  );
}

/** Standard page-width section wrapper. */
export function Section({
  children,
  className,
  id,
}: {
  children: ReactNode;
  className?: string;
  id?: string;
}) {
  return (
    <section id={id} className={cn("relative py-24 md:py-36", className)}>
      {children}
    </section>
  );
}

/** Two-column prose block used across editorial pages. */
export function ProseBlock({
  label,
  title,
  children,
  flip = false,
}: {
  label: string;
  title: string;
  children: ReactNode;
  flip?: boolean;
}) {
  return (
    <Section>
      <div className="container-page">
        <div className="grid gap-10 md:grid-cols-12 md:gap-16">
          <Reveal
            className={cn("md:col-span-4", flip && "md:order-2")}
            y={24}
          >
            <SectionLabel>{label}</SectionLabel>
            <h2 className="text-3xl font-light leading-tight tracking-tight text-fg-primary md:text-4xl">
              {title}
            </h2>
          </Reveal>
          <Reveal
            className="md:col-span-7 md:col-start-6"
            y={24}
            delay={0.12}
          >
            <div className="space-y-5 text-[15px] leading-[1.85] text-fg-mute">
              {children}
            </div>
          </Reveal>
        </div>
      </div>
    </Section>
  );
}
