# Deploying to Modal

## Prerequisites

1. [Modal account](https://modal.com) + CLI installed:
   ```bash
   pip install modal
   modal setup
   ```

2. Create a Modal secret called `pickleball-secrets`:
   ```bash
   modal secret create pickleball-secrets \
     GEMINI_API_KEY=your_gemini_key \
     OPENAI_API_KEY=your_openai_key
   ```
   (Only need one — Gemini is default and cheaper)

## Deploy

```bash
# Deploy to production
modal deploy modal_app.py

# Or test locally first
modal serve modal_app.py
```

This gives you a URL like: `https://your-username--pickleball-analytics-web.modal.run`

## Frontend

1. Set the Modal API URL:
   ```bash
   cd frontend
   echo "NEXT_PUBLIC_API_URL=https://your-username--pickleball-analytics-web.modal.run" > .env.production
   ```

2. Deploy to Vercel:
   ```bash
   npx vercel --prod
   ```

## Architecture

```
User → Vercel (Next.js) → Modal API
                            ├── download_video()     — CPU, downloads YouTube
                            ├── run_cv_pass()        — T4 GPU, YOLO + tracking
                            ├── run_llm_batch() ×N   — CPU, parallel LLM calls
                            └── compute_stats()      — CPU, merges everything
```

All functions scale to zero when idle. You only pay for active compute.

## Costs

| Component | Per video (20 min) |
|---|---|
| GPU (T4, ~90s) | ~$0.015 |
| LLM (Gemini Flash) | ~$0.03-0.08 |
| CPU functions | ~$0.001 |
| **Total (hybrid)** | **~$0.05-0.10** |
| **Total (CV only)** | **~$0.02** |

## Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/analyze` | POST | Analyze YouTube URL `{"url": "...", "mode": "cv\|hybrid"}` |
| `/analyze/upload` | POST | Upload video file (multipart form) |
| `/health` | GET | Health check |

## Volume

Downloaded videos are cached in a Modal Volume (`pickleball-data`). 
Same YouTube video won't be re-downloaded on subsequent analyses.
