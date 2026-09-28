import * as Accordion from "@radix-ui/react-accordion";
import { ChevronDown } from "lucide-react";
import { Reveal } from "@/animations/Reveal";
import { SplitText } from "@/animations/SplitText";
import { Section, SectionLabel } from "@/components/Section";
import { faqGroups } from "@/data/faq";

export default function FAQ() {
  return (
    <>
      <section className="relative overflow-hidden pb-14 pt-40 md:pt-52">
        <div
          aria-hidden="true"
          className="absolute inset-0"
          style={{
            background:
              "radial-gradient(ellipse 55% 45% at 40% 0%, #131313 0%, #080808 60%)",
          }}
        />
        <div className="container-page relative z-10">
          <SectionLabel>FAQ</SectionLabel>
          <h1 className="max-w-5xl text-[clamp(2.6rem,7vw,5.4rem)] font-extralight leading-[1.02] tracking-tight text-fg-primary">
            <SplitText mode="fall" stagger={0.05}>
              Questions, answered
            </SplitText>
            <br />
            <span className="text-fg-dim">
              <SplitText mode="fall" stagger={0.05} delay={0.2}>
                precisely.
              </SplitText>
            </span>
          </h1>
        </div>
      </section>

      <Section className="border-t border-line">
        <div className="container-page max-w-3xl">
          {faqGroups.map((group, gi) => (
            <div key={group.group} className={gi > 0 ? "mt-16" : ""}>
              <Reveal y={16}>
                <SectionLabel>{group.group}</SectionLabel>
              </Reveal>
              <Reveal y={18} delay={0.05}>
                <Accordion.Root type="single" collapsible className="space-y-2">
                  {group.items.map((item, i) => (
                    <Accordion.Item
                      key={item.q}
                      value={`${group.group}-${i}`}
                      className="overflow-hidden rounded-lg border border-line bg-ink-900 transition-colors data-[state=open]:bg-ink-800"
                    >
                      <Accordion.Header>
                        <Accordion.Trigger className="group flex w-full items-center justify-between gap-4 px-6 py-5 text-left">
                          <span className="text-[15px] text-fg-body transition-colors group-data-[state=open]:text-fg-primary">
                            {item.q}
                          </span>
                          <ChevronDown
                            className="h-4 w-4 shrink-0 text-fg-dim transition-transform duration-200 group-data-[state=open]:rotate-180"
                            aria-hidden="true"
                          />
                        </Accordion.Trigger>
                      </Accordion.Header>
                      <Accordion.Content className="overflow-hidden data-[state=closed]:animate-none">
                        <p className="border-t border-line px-6 py-5 text-[14px] leading-[1.8] text-fg-mute">
                          {item.a}
                        </p>
                      </Accordion.Content>
                    </Accordion.Item>
                  ))}
                </Accordion.Root>
              </Reveal>
            </div>
          ))}
        </div>
      </Section>
    </>
  );
}
