import { useCallback, useEffect, useRef, useState } from "react";
import {
  Play,
  Pause,
  Volume2,
  VolumeX,
  Maximize,
  Loader2,
  AlertTriangle,
  RotateCcw,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useReducedMotion } from "@/hooks/useReducedMotion";

type Props = {
  src: string;
  title?: string;
  /** Poster image path; falls back to a generated first-frame pause. */
  poster?: string;
  className?: string;
  /** Start muted+autoplaying+looping as an ambient background visual. */
  ambient?: boolean;
  preload?: "auto" | "metadata" | "none";
};

/**
 * SyncNode product video player.
 * Custom accessible controls; ambient mode for cinematic background use.
 * Lazy by default — media is only fetched when the component mounts in view
 * (wrap it in a section that conditionally renders, or rely on preload).
 */
export function ProductVideo({
  src,
  title,
  poster,
  className,
  ambient = false,
  preload = "metadata",
}: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const shellRef = useRef<HTMLDivElement>(null);
  const [playing, setPlaying] = useState(ambient);
  const [muted, setMuted] = useState(ambient);
  const [progress, setProgress] = useState(0);
  const [duration, setDuration] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [started, setStarted] = useState(ambient);
  const reduced = useReducedMotion();

  // Respect reduced motion for ambient autoplay.
  useEffect(() => {
    if (ambient && reduced && videoRef.current) {
      videoRef.current.pause();
      setPlaying(false);
    }
  }, [ambient, reduced]);

  const togglePlay = useCallback(() => {
    const v = videoRef.current;
    if (!v) return;
    if (v.paused) {
      v.play().catch(() => setError(true));
    } else {
      v.pause();
    }
  }, []);

  const toggleMute = useCallback(() => {
    const v = videoRef.current;
    if (!v) return;
    v.muted = !v.muted;
    setMuted(v.muted);
  }, []);

  const restart = useCallback(() => {
    const v = videoRef.current;
    if (!v) return;
    v.currentTime = 0;
    v.play().catch(() => setError(true));
  }, []);

  const toggleFullscreen = useCallback(() => {
    const shell = shellRef.current;
    if (!shell) return;
    if (document.fullscreenElement) {
      document.exitFullscreen().catch(() => {});
    } else {
      shell.requestFullscreen?.().catch(() => {});
    }
  }, []);

  const onTimeUpdate = () => {
    const v = videoRef.current;
    if (!v || !v.duration) return;
    setProgress(v.currentTime / v.duration);
  };

  const onLoaded = () => {
    setLoading(false);
    setError(false);
    if (videoRef.current) setDuration(videoRef.current.duration);
  };

  const onError = () => {
    setLoading(false);
    setError(true);
  };

  const fmt = (s: number) => {
    if (!Number.isFinite(s)) return "0:00";
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return `${m}:${sec.toString().padStart(2, "0")}`;
  };

  return (
    <div
      ref={shellRef}
      className={cn(
        "group relative overflow-hidden rounded-lg border border-line bg-black",
        className
      )}
    >
      <video
        ref={videoRef}
        src={started ? src : undefined}
        poster={poster}
        muted={muted}
        loop={ambient}
        playsInline
        autoPlay={ambient && !reduced}
        preload={started ? preload : "none"}
        aria-label={title ?? "SyncNode product video"}
        className="h-full w-full object-cover"
        onPlay={() => setPlaying(true)}
        onPause={() => setPlaying(false)}
        onTimeUpdate={onTimeUpdate}
        onLoadedMetadata={onLoaded}
        onError={onError}
        onCanPlay={() => setLoading(false)}
        onClick={ambient ? undefined : togglePlay}
      />

      {/* Loading state */}
      {loading && !error && (
        <div className="absolute inset-0 flex items-center justify-center bg-ink-950/60">
          <Loader2 className="h-6 w-6 animate-spin text-fg-dim" aria-label="Loading video" />
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-ink-950/80 p-6 text-center">
          <AlertTriangle className="h-5 w-5 text-warn" />
          <p className="font-mono text-micro-sm uppercase tracking-wider2 text-fg-mute">
            Video unavailable
          </p>
          <button
            onClick={restart}
            className="btn-ghost btn-md border border-line"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            Retry
          </button>
        </div>
      )}

      {/* Click-to-start overlay (non-ambient) */}
      {!ambient && !started && !error && (
        <button
          className="absolute inset-0 flex w-full items-center justify-center bg-ink-950/40 transition-colors hover:bg-ink-950/20"
          onClick={() => {
            setStarted(true);
            // start after src is set
            requestAnimationFrame(() => {
              videoRef.current?.play().catch(() => {});
            });
          }}
          aria-label={`Play ${title ?? "video"}`}
        >
          <span className="flex h-16 w-16 items-center justify-center rounded-full border border-fg-dim bg-ink-950/60 backdrop-blur-sm transition-all hover:scale-105 hover:border-fg-primary">
            <Play className="ml-0.5 h-5 w-5 text-fg-primary" />
          </span>
        </button>
      )}

      {/* Controls */}
      {!ambient && started && !error && (
        <div
          className={cn(
            "absolute inset-x-0 bottom-0 flex items-center gap-3 bg-gradient-to-t from-black/85 to-transparent px-4 pb-3 pt-10 opacity-0 transition-opacity duration-300",
            "group-hover:opacity-100 focus-within:opacity-100"
          )}
        >
          <button
            onClick={togglePlay}
            aria-label={playing ? "Pause" : "Play"}
            className="text-fg-primary transition-colors hover:text-white"
          >
            {playing ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
          </button>

          <div
            className="relative h-1 flex-1 cursor-pointer rounded-full bg-white/15"
            role="slider"
            aria-label="Seek"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={Math.round(progress * 100)}
            tabIndex={0}
            onClick={(e) => {
              const v = videoRef.current;
              if (!v || !v.duration) return;
              const rect = e.currentTarget.getBoundingClientRect();
              v.currentTime = ((e.clientX - rect.left) / rect.width) * v.duration;
            }}
            onKeyDown={(e) => {
              const v = videoRef.current;
              if (!v) return;
              if (e.key === "ArrowRight") v.currentTime += 5;
              if (e.key === "ArrowLeft") v.currentTime -= 5;
            }}
          >
            <div
              className="absolute inset-y-0 left-0 rounded-full bg-fg-primary"
              style={{ width: `${progress * 100}%` }}
            />
          </div>

          <span className="font-mono text-[10px] text-fg-mute">
            {fmt(progress * duration)}
          </span>

          <button
            onClick={toggleMute}
            aria-label={muted ? "Unmute" : "Mute"}
            className="text-fg-primary transition-colors hover:text-white"
          >
            {muted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
          </button>

          <button
            onClick={toggleFullscreen}
            aria-label="Fullscreen"
            className="text-fg-primary transition-colors hover:text-white"
          >
            <Maximize className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  );
}
