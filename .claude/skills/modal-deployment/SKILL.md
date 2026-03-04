# Modal Deployment

## Current Setup
- **App name:** `pickleball-analytics`
- **File:** `modal_app.py` in repo root
- **GPU:** T4 for CV pass
- **Volume:** `pickleball-data` at `/data` for video cache + results
- **Secrets:** `pickleball-secrets` (GEMINI_API_KEY, OPENAI_API_KEY)

## Functions

| Function | Compute | Purpose |
|----------|---------|---------|
| `download_video()` | CPU | yt-dlp YouTube download → volume cache |
| `run_cv_pass()` | T4 GPU | YOLO + ByteTrack + court detection |
| `run_llm_batch()` | CPU | Vision LLM call (one batch of frames) |
| `compute_stats()` | CPU | Merge CV + LLM → final MatchStats |
| `web()` | CPU | FastAPI ASGI app |

## API Endpoints

| Endpoint | Method | Body |
|----------|--------|------|
| `/analyze` | POST | `{"url": "youtube_url", "mode": "cv\|hybrid", "max_seconds": 0}` |
| `/analyze/upload` | POST | multipart form: `video` file + `mode` + `max_seconds` query params |
| `/health` | GET | Returns `{"status": "ok"}` |

## Deploy Commands
```bash
modal deploy modal_app.py      # production
modal serve modal_app.py       # dev (hot reload)
modal app list                 # see deployed apps
modal app logs pickleball-analytics  # view logs
```

## Image Dependencies
The Modal image installs: ffmpeg, libgl1, nodejs (for yt-dlp), all Python packages, and pre-downloads yolov8n.pt.

## Adding New Dependencies
Edit the `image = (modal.Image.debian_slim(...)` block in `modal_app.py`. System packages go in `.apt_install()`, Python packages in `.pip_install()`.

## Key Patterns
- Use `.remote()` for synchronous function calls
- Use `.spawn()` for parallel execution (returns future, call `.get()` to collect)
- Volume needs `.commit()` after writes to persist
- `@modal.concurrent(max_inputs=N)` for concurrent web requests
- `@modal.asgi_app()` wraps FastAPI as a Modal web function

## Gotchas
- `allow_concurrent_inputs` is deprecated → use `@modal.concurrent()` decorator
- File uploads need `python-multipart` pip package
- yt-dlp needs `nodejs` apt package for YouTube JS extraction
- Volume data persists across deploys but not across `modal.Volume.from_name()` name changes
- GPU cold starts: ~30-60s first request (YOLO model loading), warm after that
