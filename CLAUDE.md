# Pickleball Analytics — Agent Guide

## What This Is
AI-powered pickleball match video analysis. Upload a video (or paste YouTube URL) → CV detects players/ball/court → AI classifies shots → stats dashboard.

## Architecture

```
Frontend (Next.js)  →  Modal API (serverless)
                         ├── download_video()     — CPU, yt-dlp
                         ├── run_cv_pass()        — T4 GPU, YOLO + ByteTrack
                         ├── run_llm_batch() ×N   — CPU, Gemini/GPT-4o (parallel)
                         └── compute_stats()      — CPU, merge + aggregate
```

### Two Analysis Modes
- **CV Only (`cv`)**: YOLO + ByteTrack + heuristic shot classifier. Free, fast, offline.
- **Hybrid (`hybrid`)**: Same CV + vision LLM for shot classification. More accurate, ~$0.05/video.

## Project Structure

```
src/
├── detection/
│   ├── player_detector.py   # YOLOv8 person detection, filter to 4 players
│   └── ball_detector.py     # YOLO sports ball + HSV color fallback
├── tracking/
│   └── tracker.py           # ByteTrack multi-object + ball trajectory
├── court/
│   └── court_detector.py    # Hough lines → corners → homography → court coords (feet)
├── analysis/
│   ├── shot_classifier.py   # Heuristic classifier (CV-only mode)
│   ├── llm_classifier.py    # Vision LLM classifier (hybrid mode)
│   └── stats.py             # StatsAggregator → MatchStats (Pydantic models)
├── pipeline.py              # AnalysisPipeline — orchestrates CV/LLM/stats
├── downloader.py            # YouTube download via yt-dlp
├── main.py                  # CLI entry point (typer)
└── api/
    └── server.py            # Local FastAPI server (dev)

modal_app.py                 # Modal deployment — GPU functions + web API
frontend/                    # Next.js dashboard
research/                    # Competitive analysis docs
```

## Key Data Models

### Detection → Tracking → Classification → Stats

```
PlayerDetector.detect(frame) → Detection(bbox, confidence)
    ↓
MultiObjectTracker.update_players() → TrackedPlayer(tracker_id, team, positions[])
    ↓
ShotClassifier.classify() → Shot(shot_type, outcome, player_id, team, ball_speed)
    ↓
Rally(shots[], point_winner_team, ending_type)
    ↓
StatsAggregator.compute() → MatchStats(players[], teams[], rallies[], shot_distribution)
```

### Shot Types (current)
`serve`, `return`, `dink`, `drive`, `drop`, `lob`, `volley`, `overhead`, `unknown`

### Shot Types (need to add)
`erne`, `atp`, `reset`, `speedup`, `passing`, `poach`

### Court Coordinates
- Origin: near-side left corner
- Units: feet
- Court: 20ft wide × 44ft long
- Kitchen: 7ft from net on each side
- Net at Y=22ft

### Zones
`near_baseline`, `near_transition`, `near_kitchen`, `far_kitchen`, `far_transition`, `far_baseline`, `out_of_bounds`

## Commands

```bash
# CLI (local)
python -m src.main "video.mp4" --mode cv
python -m src.main "https://youtube.com/watch?v=..." --mode hybrid

# Modal (deploy)
modal deploy modal_app.py
modal serve modal_app.py  # dev

# Frontend
cd frontend && npm run dev

# API (local dev)
python -m src.api.server
```

## Git Conventions
- No Co-Authored-By
- Conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`
- Username: 2manslkh / kenghin_lim@hotmail.com

## Key Dependencies
- `ultralytics` — YOLOv8
- `supervision` — ByteTrack
- `opencv-python-headless` — CV ops
- `google-generativeai` / `openai` — LLM providers
- `yt-dlp` — YouTube download
- `fastapi` + `pydantic` — API + models
- `typer` — CLI
- `loguru` — logging

## Competitor Context
See `research/` for PB Vision analysis. Key gaps we're targeting:
- Their processing takes 30min-24hrs (ours: 1-2min)
- They charge $100-400/yr (ours: $0.05/video)
- They can't analyze YouTube videos (we can)
- They don't support drills or rally scoring (we will)
