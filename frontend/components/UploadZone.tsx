"use client";

import { useState, useCallback } from "react";

interface UploadZoneProps {
  onUpload: (file: File) => void;
  isProcessing: boolean;
  progress: number;
}

export default function UploadZone({ onUpload, isProcessing, progress }: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file && file.type.startsWith("video/")) {
        onUpload(file);
      }
    },
    [onUpload]
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) onUpload(file);
    },
    [onUpload]
  );

  if (isProcessing) {
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
            {progress < 30
              ? "🔍 Detecting players & ball..."
              : progress < 70
                ? "🧠 AI analyzing shots & rallies..."
                : "📊 Computing statistics..."}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`flex flex-col items-center justify-center h-[60vh] border-2 border-dashed rounded-2xl transition-colors cursor-pointer ${
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
      <div className="text-6xl mb-4">🏓</div>
      <div className="text-xl font-semibold mb-2">Drop your match video here</div>
      <div className="text-sm text-[var(--text-secondary)]">
        or click to browse — MP4, MOV, AVI supported
      </div>
    </div>
  );
}
