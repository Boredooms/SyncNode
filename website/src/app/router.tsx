import { lazy, Suspense, type ComponentType } from "react";
import { PageTransition } from "@/components/PageTransition";

const Home = lazy(() => import("@/pages/Home"));
const About = lazy(() => import("@/pages/About"));
const Features = lazy(() => import("@/pages/Features"));
const Workflow = lazy(() => import("@/pages/Workflow"));
const Demo = lazy(() => import("@/pages/Demo"));
const Architecture = lazy(() => import("@/pages/Architecture"));
const Security = lazy(() => import("@/pages/Security"));
const UseCases = lazy(() => import("@/pages/UseCases"));
const Download = lazy(() => import("@/pages/Download"));
const FAQ = lazy(() => import("@/pages/FAQ"));
const Roadmap = lazy(() => import("@/pages/Roadmap"));
const NotFound = lazy(() => import("@/pages/NotFound"));

function withTransition(C: ComponentType) {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-[60vh] items-center justify-center">
          <span className="font-mono text-micro uppercase tracking-wider2 text-fg-faint">
            Loading…
          </span>
        </div>
      }
    >
      <PageTransition>
        <C />
      </PageTransition>
    </Suspense>
  );
}

export const routes = [
  { path: "/", element: withTransition(Home) },
  { path: "/about", element: withTransition(About) },
  { path: "/features", element: withTransition(Features) },
  { path: "/workflow", element: withTransition(Workflow) },
  { path: "/demo", element: withTransition(Demo) },
  { path: "/architecture", element: withTransition(Architecture) },
  { path: "/security", element: withTransition(Security) },
  { path: "/use-cases", element: withTransition(UseCases) },
  { path: "/download", element: withTransition(Download) },
  { path: "/faq", element: withTransition(FAQ) },
  { path: "/roadmap", element: withTransition(Roadmap) },
  { path: "*", element: withTransition(NotFound) },
];
