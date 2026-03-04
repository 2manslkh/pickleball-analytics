/**
 * API client for Pickleball Analytics.
 *
 * In production, calls go to Modal's serverless API.
 * In dev, proxied to localhost:8000 via next.config.ts rewrites.
 */

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || // Modal URL in production
  ""; // Empty = use Next.js proxy in dev

export type AnalysisMode = "cv" | "hybrid";

export interface AnalyzeOptions {
  mode: AnalysisMode;
  llmProvider?: string;
}

/**
 * Analyze a YouTube video. Returns stats directly (Modal handles everything server-side).
 */
export async function analyzeYouTube(url: string, options: AnalyzeOptions) {
  const res = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      url,
      mode: options.mode,
      llm_provider: options.llmProvider || "gemini",
    }),
  });

  if (!res.ok) {
    const error = await res.text();
    throw new Error(`Analysis failed: ${error}`);
  }

  return res.json();
}

/**
 * Upload and analyze a local video file.
 */
export async function analyzeUpload(file: File, options: AnalyzeOptions) {
  const formData = new FormData();
  formData.append("video", file);

  const res = await fetch(
    `${API_BASE}/analyze/upload?mode=${options.mode}`,
    {
      method: "POST",
      body: formData,
    }
  );

  if (!res.ok) {
    const error = await res.text();
    throw new Error(`Analysis failed: ${error}`);
  }

  return res.json();
}
