# 🏓 Pickleball Match Analytics

AI-powered video analysis for pickleball doubles matches. Upload a match video, get detailed stats on every player's performance.

## What It Does

- **Player Detection & Tracking** — Tracks all 4 players throughout the match using YOLO + ByteTrack
- **Ball Tracking** — Detects and tracks the ball frame-by-frame
- **Court Detection** — Maps the court lines for spatial analysis
- **Shot Classification** — Identifies dinks, drives, drops, lobs, volleys, serves
- **Match Stats** — Generates a comprehensive performance report

## Stats Generated

| Category | Metrics |
|----------|---------|
| **Shots** | Total shots, dinks, drives, drops, lobs, volleys, serves |
| **Accuracy** | Dink accuracy, 3rd shot drop success rate, serve in % |
| **Errors** | Unforced errors, forced errors, error types |
| **Positioning** | Kitchen line time %, court coverage heat map |
| **Rally** | Avg rally length, point-ending shot types |
| **Strategy** | 3rd shot selection, transition success rate |

## Architecture — Hybrid (CV + LLM)

**Phase 1 (CV):** YOLOv8 detects players + ball → ByteTrack maintains persistent IDs → Court homography maps positions to real-world coordinates.

**Phase 2 (LLM):** Annotated frame batches are sent to a vision LLM (Gemini 2.5 Pro / GPT-4o) for shot classification, rally analysis, and game event detection.

**Phase 3 (Stats):** CV tracking data + LLM analysis are merged into final statistics.

### Why Hybrid?
- CV is great at **detection and tracking** (precise, fast, deterministic)
- LLMs are great at **understanding game context** (shot intent, rally dynamics, strategy)
- Heuristic classifiers are brittle; LLMs handle edge cases naturally

## Tech Stack

- **Detection:** YOLOv8 (players + ball)
- **Tracking:** ByteTrack (multi-object tracking)
- **Court:** OpenCV homography + line detection
- **Shot Analysis:** Vision LLM (Gemini 2.5 Pro / GPT-4o)
- **Backend:** FastAPI
- **Frontend:** Next.js
- **Processing:** OpenCV + ffmpeg

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run analysis on a video (default: Gemini)
python -m src.main analyze --video path/to/match.mp4

# Use GPT-4o instead
python -m src.main analyze --video path/to/match.mp4 --llm openai

# Start the API server
python -m src.api.server

# Start the frontend
cd frontend && npm run dev
```

## Project Structure

```
src/
├── detection/      # YOLO player + ball detection
├── tracking/       # Multi-object tracking (ByteTrack)
├── court/          # Court line detection + homography
├── analysis/       # Shot classification + stats aggregation
├── api/            # FastAPI backend
main.py             # CLI entry point
frontend/           # Next.js dashboard
models/             # Trained model weights
data/
├── videos/         # Input match videos
└── outputs/        # Analysis results
```

## License

MIT
