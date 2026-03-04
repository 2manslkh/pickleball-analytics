"use client";

import { useState, useCallback } from "react";

export type AnalysisMode = "cv" | "hybrid";

interface UploadZoneProps {
  onUpload: (file: File, mode: AnalysisMode) => void;
  onYouTubeSubmit: (url: string, mode: AnalysisMode) => void;
  isProcessing: boolean;
  progress: number;
  processingStatus?: string;
}

const YOUTUBE_REGEX =
  /^(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/shorts\/)[a-zA-Z0-9_-]{11}/;

export default function UploadZone({
  onUpload,
  onYouTubeSubmit,
  isProcessing,
  progress,
  processingStatus,
}: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [urlError, setUrlError] = useState("");
  const [mode, setMode] = useState<AnalysisMode>("hybrid");

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file && file.type.startsWith("video/")) {
        onUpload(file, mode);
      }
    },
    [onUpload]
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) onUpload(file, mode);
    },
    [onUpload]
  );

  const handleYouTubeSubmit = useCallback(() => {
    const url = youtubeUrl.trim();
    if (!url) return;
    if (!YOUTUBE_REGEX.test(url)) {
      setUrlError("Invalid YouTube URL");
      return;
    }
    setUrlError("");
    onYouTubeSubmit(url, mode);
  }, [youtubeUrl, onYouTubeSubmit]);

  if (isProcessing) {
    const statusMessage =
      processingStatus ||
      (progress < 15
        ? "📥 Downloading video..."
        : progress < 40
          ? "🔍 Detecting players & ball..."
          : progress < 75
            ? "🧠 AI analyzing shots & rallies..."
            : "📊 Computing statistics...");

    return (
      <div className="flex flex-col items-center justify-center h-[60vh] gap-6">
        <div className="relative w-32 h-32">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 120 120">
            <circle
              cx="60" cy="60" r="54"
              fill="none" stroke="var(--border)" strokeWidth="8"
            />
            <circle
              cx="60" cy="60" r="54"
              fill="none" stroke="var(--accent)" strokeWidth="8"
              strokeDasharray={`${2 * Math.PI * 54}`}
              strokeDashoffset={`${2 * Math.PI * 54 * (1 - progress / 100)}`}
              strokeLinecap="round"
              className="transition-all duration-500"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-2xl font-bold">{Math.round(progress)}%</span>
          </div>
        </div>
        <div className="text-center">
          <div className="text-lg font-semibold">Analyzing match...</div>
          <div className="text-sm text-[var(--text-secondary)] mt-1">
            {statusMessage}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-6">
      {/* YouTube URL Input */}
      <div className="w-full max-w-xl">
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <input
              type="text"
              placeholder="Paste YouTube link here..."
              value={youtubeUrl}
              onChange={(e) => {
                setYoutubeUrl(e.target.value);
                setUrlError("");
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleYouTubeSubmit();
              }}
              className="w-full px-4 py-3 rounded-xl bg-[var(--bg-card)] border border-[var(--border)] text-[var(--text)] placeholder:text-[var(--text-secondary)] focus:outline-none focus:border-[var(--accent)] transition-colors"
            />
            {youtubeUrl && (
              <button
                onClick={() => {
                  setYoutubeUrl("");
                  setUrlError("");
                }}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-secondary)] hover:text-[var(--text)]"
              >
                ✕
              </button>
            )}
          </div>
          <button
            onClick={handleYouTubeSubmit}
            disabled={!youtubeUrl.trim()}
            className="px-5 py-3 rounded-xl bg-red-600 hover:bg-red-700 disabled:opacity-30 disabled:cursor-not-allowed font-semibold text-sm transition-colors flex items-center gap-2"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="white">
              <path d="M23.5 6.2c-.3-1-1-1.8-2-2.1C19.6 3.5 12 3.5 12 3.5s-7.6 0-9.5.6c-1 .3-1.7 1.1-2 2.1C0 8.1 0 12 0 12s0 3.9.5 5.8c.3 1 1 1.8 2 2.1 1.9.6 9.5.6 9.5.6s7.6 0 9.5-.6c1-.3 1.7-1.1 2-2.1.5-1.9.5-5.8.5-5.8s0-3.9-.5-5.8zM9.5 15.6V8.4l6.3 3.6-6.3 3.6z" />
            </svg>
            Analyze
          </button>
        </div>
        {urlError && (
          <div className="text-red-400 text-xs mt-1.5 ml-1">{urlError}</div>
        )}
      </div>

      {/* Mode Toggle */}
      <div className="w-full max-w-xl">
        <div className="flex items-center gap-1 p-1 bg-[var(--bg-card)] border border-[var(--border)] rounded-xl">
          <button
            onClick={() => setMode("cv")}
            className={`flex-1 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
              mode === "cv"
                ? "bg-[var(--accent)] text-black"
                : "text-[var(--text-secondary)] hover:text-[var(--text)] hover:bg-[var(--bg-card-hover)]"
            }`}
          >
            <div className="font-semibold">⚡ CV Only</div>
            <div className={`text-[10px] mt-0.5 ${mode === "cv" ? "text-black/60" : "text-[var(--text-secondary)]"}`}>
              Free · Fast · Offline
            </div>
          </button>
          <button
            onClick={() => setMode("hybrid")}
            className={`flex-1 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
              mode === "hybrid"
                ? "bg-[var(--accent)] text-black"
                : "text-[var(--text-secondary)] hover:text-[var(--text)] hover:bg-[var(--bg-card-hover)]"
            }`}
          >
            <div className="font-semibold">🧠 Hybrid CV + AI</div>
            <div className={`text-[10px] mt-0.5 ${mode === "hybrid" ? "text-black/60" : "text-[var(--text-secondary)]"}`}>
              More accurate · ~$0.03–2/video
            </div>
          </button>
        </div>
      </div>

      {/* Divider */}
      <div className="flex items-center gap-3 w-full max-w-xl">
        <div className="flex-1 h-px bg-[var(--border)]" />
        <span className="text-xs text-[var(--text-secondary)]">or</span>
        <div className="flex-1 h-px bg-[var(--border)]" />
      </div>

      {/* File Drop Zone */}
      <div
        className={`w-full flex flex-col items-center justify-center h-[40vh] border-2 border-dashed rounded-2xl transition-colors cursor-pointer ${
          isDragging
            ? "border-[var(--accent)] bg-[var(--accent)]/5"
            : "border-[var(--border)] hover:border-[var(--text-secondary)]"
        }`}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => document.getElementById("file-input")?.click()}
      >
        <input
          id="file-input"
          type="file"
          accept="video/*"
          className="hidden"
          onChange={handleFileSelect}
        />
        <div className="text-5xl mb-3">📁</div>
        <div className="text-lg font-semibold mb-1">Drop your match video here</div>
        <div className="text-sm text-[var(--text-secondary)]">
          MP4, MOV, AVI supported
        </div>
      </div>
    </div>
  );
}
