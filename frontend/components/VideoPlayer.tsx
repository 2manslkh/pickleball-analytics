"use client";

import { useRef, useState, useEffect, useCallback } from "react";
import { TimelineMarker } from "@/lib/types";

interface VideoPlayerProps {
  videoUrl: string;
  markers: TimelineMarker[];
  onTimeUpdate?: (time: number) => void;
  fps?: number;
}

export default function VideoPlayer({
  videoUrl,
  markers,
  onTimeUpdate,
  fps = 30,
}: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const timelineRef = useRef<HTMLDivElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [activeMarker, setActiveMarker] = useState<TimelineMarker | null>(null);

  const handleTimeUpdate = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;
    setCurrentTime(video.currentTime);
    onTimeUpdate?.(video.currentTime);

    // Find closest marker
    const closest = markers.reduce<TimelineMarker | null>((best, m) => {
      const diff = Math.abs(m.time - video.currentTime);
      if (diff < 0.5) {
        if (!best || diff < Math.abs(best.time - video.currentTime)) return m;
      }
      return best;
    }, null);
    setActiveMarker(closest);
  }, [markers, onTimeUpdate]);

  const seekTo = useCallback((time: number) => {
    const video = videoRef.current;
    if (video) {
      video.currentTime = time;
      setCurrentTime(time);
    }
  }, []);

  const togglePlay = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;
    if (video.paused) {
      video.play();
      setIsPlaying(true);
    } else {
      video.pause();
      setIsPlaying(false);
    }
  }, []);

  const stepFrame = useCallback(
    (direction: 1 | -1) => {
      const video = videoRef.current;
      if (!video) return;
      video.pause();
      setIsPlaying(false);
      video.currentTime += direction / fps;
    },
    [fps]
  );

  const jumpToMarker = useCallback(
    (direction: "prev" | "next") => {
      const sorted = [...markers].sort((a, b) => a.time - b.time);
      if (direction === "next") {
        const next = sorted.find((m) => m.time > currentTime + 0.1);
        if (next) seekTo(next.time);
      } else {
        const prev = [...sorted].reverse().find((m) => m.time < currentTime - 0.1);
        if (prev) seekTo(prev.time);
      }
    },
    [markers, currentTime, seekTo]
  );

  // Keyboard shortcuts
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement) return;
      switch (e.key) {
        case " ":
          e.preventDefault();
          togglePlay();
          break;
        case "ArrowLeft":
          e.shiftKey ? jumpToMarker("prev") : stepFrame(-1);
          break;
        case "ArrowRight":
          e.shiftKey ? jumpToMarker("next") : stepFrame(1);
          break;
        case ",":
          stepFrame(-1);
          break;
        case ".":
          stepFrame(1);
          break;
      }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [togglePlay, stepFrame, jumpToMarker]);

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return `${m}:${sec.toString().padStart(2, "0")}`;
  };

  const handleTimelineClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const pct = (e.clientX - rect.left) / rect.width;
    seekTo(pct * duration);
  };

  const shotColors: Record<string, string> = {
    serve: "#3b82f6",
    return: "#8b5cf6",
    dink: "#22c55e",
    drive: "#ef4444",
    drop: "#f59e0b",
    lob: "#06b6d4",
    volley: "#ec4899",
    overhead: "#f97316",
    erne: "#a855f7",
    atp: "#14b8a6",
    reset: "#64748b",
    speedup: "#dc2626",
    passing: "#0ea5e9",
    poach: "#d946ef",
  };

  return (
    <div className="flex flex-col gap-3">
      {/* Video */}
      <div className="relative rounded-xl overflow-hidden bg-black aspect-video">
        <video
          ref={videoRef}
          src={videoUrl}
          className="w-full h-full object-contain"
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={() => setDuration(videoRef.current?.duration || 0)}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
          playsInline
        />
        {/* Active marker overlay */}
        {activeMarker && (
          <div className="absolute top-4 left-4 px-3 py-1.5 rounded-lg bg-black/70 backdrop-blur-sm border border-white/10 text-sm font-medium flex items-center gap-2">
            <span
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: activeMarker.color }}
            />
            {activeMarker.label}
          </div>
        )}
      </div>

      {/* Timeline with markers */}
      <div className="relative">
        {/* Progress bar */}
        <div
          ref={timelineRef}
          className="relative h-10 bg-[var(--bg-card)] rounded-lg cursor-pointer overflow-hidden border border-[var(--border)]"
          onClick={handleTimelineClick}
        >
          {/* Progress fill */}
          <div
            className="absolute top-0 left-0 h-full bg-white/5 transition-[width] duration-100"
            style={{ width: `${(currentTime / duration) * 100}%` }}
          />

          {/* Shot markers */}
          {markers.map((marker, i) => (
            <div
              key={i}
              className="absolute top-0 h-full flex flex-col items-center justify-center cursor-pointer group"
              style={{ left: `${(marker.time / duration) * 100}%` }}
              onClick={(e) => {
                e.stopPropagation();
                seekTo(marker.time);
              }}
            >
              <div
                className="w-1 h-5 rounded-full opacity-80 group-hover:opacity-100 group-hover:scale-y-125 transition-all"
                style={{ backgroundColor: marker.color }}
              />
              {/* Tooltip */}
              <div className="absolute bottom-full mb-2 hidden group-hover:block z-10">
                <div className="px-2 py-1 rounded bg-black/90 text-xs whitespace-nowrap border border-white/10">
                  {marker.label}
                  <span className="text-[var(--text-secondary)] ml-1">
                    {formatTime(marker.time)}
                  </span>
                </div>
              </div>
            </div>
          ))}

          {/* Playhead */}
          <div
            className="absolute top-0 w-0.5 h-full bg-white z-10"
            style={{ left: `${(currentTime / duration) * 100}%` }}
          />
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            onClick={() => jumpToMarker("prev")}
            className="px-2 py-1 rounded bg-[var(--bg-card)] border border-[var(--border)] hover:bg-[var(--bg-card-hover)] text-sm"
            title="Previous event (Shift+←)"
          >
            ⏮
          </button>
          <button
            onClick={() => stepFrame(-1)}
            className="px-2 py-1 rounded bg-[var(--bg-card)] border border-[var(--border)] hover:bg-[var(--bg-card-hover)] text-sm"
            title="Previous frame (←)"
          >
            ◀
          </button>
          <button
            onClick={togglePlay}
            className="px-4 py-1.5 rounded-lg bg-[var(--accent)] text-black font-semibold hover:bg-[var(--accent-dim)] text-sm"
          >
            {isPlaying ? "⏸ Pause" : "▶ Play"}
          </button>
          <button
            onClick={() => stepFrame(1)}
            className="px-2 py-1 rounded bg-[var(--bg-card)] border border-[var(--border)] hover:bg-[var(--bg-card-hover)] text-sm"
            title="Next frame (→)"
          >
            ▶
          </button>
          <button
            onClick={() => jumpToMarker("next")}
            className="px-2 py-1 rounded bg-[var(--bg-card)] border border-[var(--border)] hover:bg-[var(--bg-card-hover)] text-sm"
            title="Next event (Shift+→)"
          >
            ⏭
          </button>
        </div>

        <span className="text-sm text-[var(--text-secondary)] tabular-nums">
          {formatTime(currentTime)} / {formatTime(duration)}
        </span>

        <div className="flex items-center gap-2">
          {[0.25, 0.5, 1, 1.5, 2].map((rate) => (
            <button
              key={rate}
              onClick={() => {
                setPlaybackRate(rate);
                if (videoRef.current) videoRef.current.playbackRate = rate;
              }}
              className={`px-2 py-0.5 rounded text-xs border ${
                playbackRate === rate
                  ? "bg-[var(--accent)] text-black border-[var(--accent)]"
                  : "bg-[var(--bg-card)] border-[var(--border)] text-[var(--text-secondary)] hover:bg-[var(--bg-card-hover)]"
              }`}
            >
              {rate}x
            </button>
          ))}
        </div>
      </div>

      {/* Shot type legend */}
      <div className="flex flex-wrap gap-3 px-1">
        {Object.entries(shotColors).map(([type, color]) => (
          <div key={type} className="flex items-center gap-1.5 text-xs text-[var(--text-secondary)]">
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
            {type}
          </div>
        ))}
      </div>
    </div>
  );
}
