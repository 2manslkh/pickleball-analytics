"use client";

import { useState, useCallback, useMemo } from "react";
import VideoPlayer from "@/components/VideoPlayer";
import StatsPanel from "@/components/StatsPanel";
import UploadZone, { AnalysisMode } from "@/components/UploadZone";
import { MatchStats, TimelineMarker } from "@/lib/types";
import { analyzeYouTube, analyzeUpload } from "@/lib/api";

// Demo data for testing UI without backend
const DEMO_STATS: MatchStats = {
  duration_seconds: 342,
  total_points: 15,
  total_rallies: 15,
  avg_rally_length: 6.2,
  longest_rally: 14,
  teams: [
    { team_id: 0, players: [], points_won: 8, points_lost: 7, side_out_pct: 0, scoring_runs: [] },
    { team_id: 1, players: [], points_won: 7, points_lost: 8, side_out_pct: 0, scoring_runs: [] },
  ],
  players: [
    {
      player_id: 1, team: 0, total_shots: 42, dinks: 15, drives: 8, drops: 6, lobs: 2,
      volleys: 5, overheads: 1, serves: 4, returns: 1, dink_accuracy: 73, third_shot_drop_attempts: 4,
      third_shot_drop_success: 75, serve_in_pct: 100, unforced_errors: 3, forced_errors: 2, winners: 4,
      kitchen_time_pct: 48, transition_time_pct: 30, baseline_time_pct: 22, avg_position: [0, 0], avg_shot_speed: 8.5, avg_rally_length: 6,
    },
    {
      player_id: 2, team: 0, total_shots: 38, dinks: 12, drives: 10, drops: 4, lobs: 3,
      volleys: 4, overheads: 0, serves: 3, returns: 2, dink_accuracy: 67, third_shot_drop_attempts: 3,
      third_shot_drop_success: 33, serve_in_pct: 100, unforced_errors: 5, forced_errors: 1, winners: 3,
      kitchen_time_pct: 35, transition_time_pct: 40, baseline_time_pct: 25, avg_position: [0, 0], avg_shot_speed: 10.2, avg_rally_length: 6,
    },
    {
      player_id: 3, team: 1, total_shots: 40, dinks: 18, drives: 5, drops: 5, lobs: 1,
      volleys: 6, overheads: 2, serves: 2, returns: 1, dink_accuracy: 82, third_shot_drop_attempts: 3,
      third_shot_drop_success: 67, serve_in_pct: 100, unforced_errors: 2, forced_errors: 3, winners: 5,
      kitchen_time_pct: 55, transition_time_pct: 25, baseline_time_pct: 20, avg_position: [0, 0], avg_shot_speed: 7.8, avg_rally_length: 6,
    },
    {
      player_id: 4, team: 1, total_shots: 35, dinks: 10, drives: 12, drops: 3, lobs: 4,
      volleys: 3, overheads: 0, serves: 2, returns: 1, dink_accuracy: 60, third_shot_drop_attempts: 2,
      third_shot_drop_success: 50, serve_in_pct: 100, unforced_errors: 6, forced_errors: 1, winners: 2,
      kitchen_time_pct: 30, transition_time_pct: 35, baseline_time_pct: 35, avg_position: [0, 0], avg_shot_speed: 11.5, avg_rally_length: 6,
    },
  ],
  rallies: [
    { number: 1, length: 5, winner_team: 0, ending: "winner", shots: ["serve", "return", "drop", "dink", "drive"] },
    { number: 2, length: 8, winner_team: 1, ending: "unforced_error", shots: ["serve", "return", "drive", "volley", "dink", "dink", "dink", "drive"] },
    { number: 3, length: 3, winner_team: 0, ending: "winner", shots: ["serve", "return", "overhead"] },
    { number: 4, length: 14, winner_team: 1, ending: "winner", shots: ["serve", "return", "drop", "dink", "dink", "dink", "drive", "volley", "dink", "dink", "lob", "overhead", "dink", "drive"] },
    { number: 5, length: 6, winner_team: 0, ending: "unforced_error", shots: ["serve", "return", "drop", "drive", "volley", "dink"] },
  ],
  shot_distribution: { dink: 55, drive: 35, drop: 18, volley: 18, serve: 11, return: 5, lob: 10, overhead: 3 },
  score_progression: [
    { point: 1, team_0: 1, team_1: 0 },
    { point: 2, team_0: 1, team_1: 1 },
    { point: 3, team_0: 2, team_1: 1 },
    { point: 4, team_0: 2, team_1: 2 },
    { point: 5, team_0: 3, team_1: 2 },
  ],
  llm_observations: [
    "Player 3 has the strongest dink game — 82% accuracy with excellent kitchen positioning",
    "Player 4 relies heavily on drives but has the highest unforced error count",
    "Team Near wins most points through 3rd shot drops → dink rallies",
    "Team Far's overhead game is their biggest weapon when they get lobs",
    "Player 2 needs to work on transition game — spends too much time in no-man's land",
  ],
};

export default function Home() {
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [stats, setStats] = useState<MatchStats | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [useDemo, setUseDemo] = useState(false);

  const handleUpload = useCallback(async (file: File, mode: AnalysisMode = "hybrid") => {
    setVideoFile(file);
    setVideoUrl(URL.createObjectURL(file));
    setIsProcessing(true);
    setProgress(10);

    try {
      setProgress(20);
      const results = await analyzeUpload(file, { mode });
      setProgress(100);
      setStats(results);
    } catch (err) {
      console.error("Upload error:", err);
      setStats(DEMO_STATS);
    } finally {
      setIsProcessing(false);
    }
  }, []);

  const handleYouTubeSubmit = useCallback(async (url: string, mode: AnalysisMode = "hybrid") => {
    setIsProcessing(true);
    setProgress(5);
    // Embed YouTube for playback
    const videoId = url.match(/(?:v=|youtu\.be\/|shorts\/)([a-zA-Z0-9_-]{11})/)?.[1];
    if (videoId) {
      setVideoUrl(`https://www.youtube.com/embed/${videoId}`);
    }

    try {
      setProgress(15);
      const results = await analyzeYouTube(url, { mode });
      setProgress(100);
      setStats(results);
    } catch (err) {
      console.error("YouTube error:", err);
      setStats(DEMO_STATS);
    } finally {
      setIsProcessing(false);
    }
  }, []);

  const handleLoadDemo = useCallback(() => {
    setStats(DEMO_STATS);
    setUseDemo(true);
  }, []);

  // Generate timeline markers from rally data
  const markers: TimelineMarker[] = useMemo(() => {
    if (!stats) return [];

    const fps = 30;
    const totalDuration = stats.duration_seconds;
    const shotColors: Record<string, string> = {
      serve: "#3b82f6",
      return: "#8b5cf6",
      dink: "#22c55e",
      drive: "#ef4444",
      drop: "#f59e0b",
      lob: "#06b6d4",
      volley: "#ec4899",
      overhead: "#f97316",
    };

    const markers: TimelineMarker[] = [];
    let timeOffset = 0;
    const avgRallyDuration = totalDuration / (stats.total_rallies || 1);

    stats.rallies.forEach((rally, ri) => {
      const rallyStart = timeOffset;

      // Rally start marker
      markers.push({
        time: rallyStart,
        type: "rally_start",
        label: `Rally #${rally.number}`,
        color: "#ffffff",
        rallyIndex: ri,
      });

      // Shot markers within rally
      const shotDuration = avgRallyDuration / (rally.length || 1);
      rally.shots.forEach((shot, si) => {
        markers.push({
          time: rallyStart + si * shotDuration,
          type: "shot",
          label: `${shot.charAt(0).toUpperCase() + shot.slice(1)}`,
          color: shotColors[shot] || "#888",
          rallyIndex: ri,
          shotType: shot,
        });
      });

      // Point marker
      if (rally.winner_team !== null) {
        markers.push({
          time: rallyStart + rally.length * shotDuration,
          type: "point",
          label: `Point → Team ${rally.winner_team === 0 ? "Near" : "Far"} (${rally.ending})`,
          color: rally.winner_team === 0 ? "#22c55e" : "#3b82f6",
          rallyIndex: ri,
        });
      }

      timeOffset += avgRallyDuration;
    });

    return markers;
  }, [stats]);

  return (
    <main className="min-h-screen p-4 lg:p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <span className="text-3xl">🏓</span>
          <div>
            <h1 className="text-xl font-bold">Pickleball Analytics</h1>
            <p className="text-xs text-[var(--text-secondary)]">
              AI-powered match analysis
            </p>
          </div>
        </div>
        {!stats && !isProcessing && (
          <button
            onClick={handleLoadDemo}
            className="px-3 py-1.5 rounded-lg text-sm border border-[var(--border)] text-[var(--text-secondary)] hover:bg-[var(--bg-card)]"
          >
            Load Demo
          </button>
        )}
        {stats && (
          <button
            onClick={() => {
              setStats(null);
              setVideoFile(null);
              setVideoUrl(null);
              setUseDemo(false);
            }}
            className="px-3 py-1.5 rounded-lg text-sm border border-[var(--border)] text-[var(--text-secondary)] hover:bg-[var(--bg-card)]"
          >
            New Analysis
          </button>
        )}
      </div>

      {/* Main content */}
      {!stats && !isProcessing ? (
        <UploadZone onUpload={handleUpload} onYouTubeSubmit={handleYouTubeSubmit} isProcessing={false} progress={0} />
      ) : isProcessing ? (
        <UploadZone onUpload={() => {}} onYouTubeSubmit={() => {}} isProcessing={true} progress={progress} />
      ) : stats ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Video + Timeline (2/3 width) */}
          <div className="lg:col-span-2">
            {videoUrl && videoUrl.includes("youtube.com/embed") ? (
              <div className="space-y-3">
                <div className="aspect-video rounded-xl overflow-hidden">
                  <iframe
                    src={videoUrl}
                    className="w-full h-full"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                  />
                </div>
              </div>
            ) : videoUrl ? (
              <VideoPlayer
                videoUrl={videoUrl}
                markers={markers}
                onTimeUpdate={setCurrentTime}
              />
            ) : (
              <div className="aspect-video bg-[var(--bg-card)] border border-[var(--border)] rounded-xl flex items-center justify-center">
                <div className="text-center text-[var(--text-secondary)]">
                  <div className="text-4xl mb-2">📊</div>
                  <div className="text-sm">Demo mode — no video loaded</div>
                  <div className="text-xs mt-1">Upload a video to see playback with markers</div>
                </div>
              </div>
            )}
          </div>

          {/* Stats Panel (1/3 width) */}
          <div className="lg:col-span-1">
            <StatsPanel stats={stats} currentTime={currentTime} />
          </div>
        </div>
      ) : null}

      {/* Keyboard shortcuts hint */}
      {stats && videoUrl && (
        <div className="fixed bottom-4 left-1/2 -translate-x-1/2 flex gap-3 text-[10px] text-[var(--text-secondary)] bg-[var(--bg-card)] border border-[var(--border)] rounded-lg px-3 py-1.5">
          <span><kbd className="px-1 bg-[var(--bg)] rounded">Space</kbd> Play/Pause</span>
          <span><kbd className="px-1 bg-[var(--bg)] rounded">←→</kbd> Frame step</span>
          <span><kbd className="px-1 bg-[var(--bg)] rounded">Shift+←→</kbd> Jump events</span>
        </div>
      )}
    </main>
  );
}
