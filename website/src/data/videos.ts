export const GITHUB_URL = "https://github.com/Boredooms/SyncNode";
export const GITHUB_RELEASES_URL = "https://github.com/Boredooms/SyncNode/releases";

/**
 * VIDEO CATALOG — verified by frame-by-frame analysis (10s each; hero master is
 * 1920x1080 HD, the rest are 4K sources).
 *
 * DELIVERY: all footage is served as 1080p H.264 (CRF 20, faststart, no audio)
 * re-encodes of the 4K masters — see frame_analysis/transcode_1080.py.
 * The 4K sources are low-bitrate; downscaling them in-browser rendered soft
 * AND cost ~2.5x the bytes. The 1080p encodes are sharper and lighter.
 *
 * Frame analysis results (of the original masters):
 * - "Website main intro.mp4"        → CENTER WORDMARK "SyncNode" + TAGLINE
 *                                     "Think Locally, Act Intelligently" + tiny
 *                                     top-left watermark. It IS a title card.
 * - "About the Project.mp4"         → "About the Project" title embedded center.
 * - "About the project 2.0.mp4"     → NO title. Animated fog. Watermark only.
 * - "Features.mp4"                  → "Features" title embedded center.
 * - "Features2.0.mp4"               → NO title. Animated vertical fog. Watermark only.
 * - "Prototype.mp4"                 → "Walkthrough the Prototype" title embedded center.
 * - "Prototype2.0.mp4"              → NO title. Animated vertical fog. Watermark only.
 *
 * RULES ENFORCED SITEWIDE:
 * 1. hasEmbeddedTitle=true  → NEVER render page text over the video. The video is a
 *    self-contained title card placed at the TOP of its section.
 * 2. hasEmbeddedTitle=false → safe to use as an ambient background under site-owned
 *    typography.
 * 3. Never reuse the same video twice on one page.
 */
export type VideoAsset = {
  id: string;
  title: string;
  src: string;
  poster: string;
  section: string;
  hasEmbeddedTitle: boolean;
  embeddedText?: string;
  description: string;
};

export const videoCatalog: Record<string, VideoAsset> = {
  hero: {
    id: "hero",
    title: "SyncNode — Main Intro",
    src: "/videos/Website main intro HD 1080p.mp4",
    poster: "/videos/posters/Website main intro HD.jpg",
    section: "home",
    hasEmbeddedTitle: true,
    embeddedText: "SyncNode — Think Locally, Act Intelligently",
    description:
      "Opening title card with the SyncNode wordmark and tagline baked in. Used as the homepage hero — the page adds no competing headline.",
  },
  aboutTitled: {
    id: "about-titled",
    title: "About the Project",
    src: "/videos/About the Project 1080p.mp4",
    poster: "/videos/posters/About the Project.jpg",
    section: "about",
    hasEmbeddedTitle: true,
    embeddedText: "About the Project",
    description:
      "Self-contained About title card. Placed at the top of /about with no overlaid text.",
  },
  aboutClean: {
    id: "about-clean",
    title: "About — Clean Ambient",
    src: "/videos/About the project 2.0 1080p.mp4",
    poster: "/videos/posters/About the project 2.0.jpg",
    section: "about",
    hasEmbeddedTitle: false,
    description:
      "Title-free animated fog. Safe as an ambient background beneath site typography.",
  },
  featuresTitled: {
    id: "features-titled",
    title: "Features",
    src: "/videos/Features 1080p.mp4",
    poster: "/videos/posters/Features.jpg",
    section: "features",
    hasEmbeddedTitle: true,
    embeddedText: "Features",
    description:
      "Self-contained Features title card. Placed at the top of /features with no overlaid text.",
  },
  featuresClean: {
    id: "features-clean",
    title: "Features — Clean Ambient",
    src: "/videos/Features2.0 1080p.mp4",
    poster: "/videos/posters/Features2.0.jpg",
    section: "features",
    hasEmbeddedTitle: false,
    description:
      "Title-free animated background. Safe beneath site-owned typography.",
  },
  prototypeTitled: {
    id: "prototype-titled",
    title: "Walkthrough the Prototype",
    src: "/videos/Prototype 1080p.mp4",
    poster: "/videos/posters/Prototype.jpg",
    section: "demo",
    hasEmbeddedTitle: true,
    embeddedText: "Walkthrough the Prototype",
    description:
      "Self-contained walkthrough title card. Main player on /demo — no overlaid text.",
  },
  prototypeClean: {
    id: "prototype-clean",
    title: "Walkthrough — Clean Ambient",
    src: "/videos/Prototype2.0 1080p.mp4",
    poster: "/videos/posters/Prototype2.0.jpg",
    section: "demo",
    hasEmbeddedTitle: false,
    description:
      "Title-free walkthrough background. Alternate cut; safe beneath typography.",
  },
};

export function videoSrc(id: keyof typeof videoCatalog | string): string {
  const v = videoCatalog[id];
  if (!v) throw new Error(`Unknown video id: ${id}`);
  return v.src;
}

export function videoPoster(id: keyof typeof videoCatalog | string): string {
  const v = videoCatalog[id];
  if (!v) throw new Error(`Unknown video id: ${id}`);
  return v.poster;
}
