import { useEffect, useState } from "react";
import {
  BrowserRouter,
  Routes,
  Route,
  useLocation,
} from "react-router-dom";
import { MotionProvider } from "@/animations/MotionProvider";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { Cursor } from "@/components/Cursor";
import { NoiseOverlay } from "@/components/NoiseOverlay";
import { BootLoader } from "@/components/BootLoader";
import { routes } from "@/app/router";
import { ScrollToTop } from "@/components/ScrollToTop";

function AnimatedRoutes() {
  const location = useLocation();
  return (
    <Routes location={location} key={location.pathname}>
      {routes.map((r) => (
        <Route key={r.path} path={r.path} element={r.element} />
      ))}
    </Routes>
  );
}

export function App() {
  const [booted, setBooted] = useState(false);

  // Freeze scroll while booting.
  useEffect(() => {
    document.documentElement.style.overflow = booted ? "" : "hidden";
    return () => {
      document.documentElement.style.overflow = "";
    };
  }, [booted]);

  return (
    <BrowserRouter>
      <MotionProvider>
        <BootLoader onComplete={() => setBooted(true)} />
        <Cursor />
        <NoiseOverlay />
        <ScrollToTop />
        <div className="relative min-h-screen bg-ink-950">
          <Header />
          <AnimatedRoutes />
          <Footer />
        </div>
      </MotionProvider>
    </BrowserRouter>
  );
}
