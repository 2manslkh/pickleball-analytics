"""FastAPI server for video upload and analysis."""

import json
import uuid
import asyncio
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from loguru import logger

from src.pipeline import AnalysisPipeline
from src.analysis.stats import MatchStats

app = FastAPI(title="🏓 Pickleball Analytics API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job store (replace with Redis/DB in production)
jobs: dict[str, dict] = {}

UPLOAD_DIR = Path("data/videos")
OUTPUT_DIR = Path("data/outputs")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class JobStatus(BaseModel):
    job_id: str
    status: str  # "queued", "processing", "complete", "error"
    progress: float = 0.0  # 0-100
    result: MatchStats | None = None
    error: str | None = None


@app.post("/analyze", response_model=dict)
async def upload_and_analyze(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
):
    """Upload a video and start analysis.

    Returns a job ID to poll for results.
    """
    # Validate file type
    if not video.filename or not video.filename.lower().endswith(
        (".mp4", ".mov", ".avi", ".mkv")
    ):
        raise HTTPException(400, "Unsupported video format. Use mp4, mov, avi, or mkv.")

    # Save uploaded file
    job_id = str(uuid.uuid4())[:8]
    ext = Path(video.filename).suffix
    video_path = UPLOAD_DIR / f"{job_id}{ext}"

    with open(video_path, "wb") as f:
        content = await video.read()
        f.write(content)

    logger.info(f"Video uploaded: {video_path} ({len(content) / 1024 / 1024:.1f}MB)")

    # Queue analysis
    jobs[job_id] = {
        "status": "queued",
        "progress": 0,
        "video_path": str(video_path),
        "result": None,
        "error": None,
    }

    background_tasks.add_task(_run_analysis, job_id, video_path)

    return {"job_id": job_id, "status": "queued"}


@app.get("/status/{job_id}", response_model=JobStatus)
async def get_status(job_id: str):
    """Check analysis job status."""
    if job_id not in jobs:
        raise HTTPException(404, f"Job {job_id} not found")

    job = jobs[job_id]
    return JobStatus(
        job_id=job_id,
        status=job["status"],
        progress=job.get("progress", 0),
        result=job.get("result"),
        error=job.get("error"),
    )


@app.get("/results/{job_id}")
async def get_results(job_id: str):
    """Get analysis results."""
    output_path = OUTPUT_DIR / f"{job_id}_stats.json"
    if not output_path.exists():
        raise HTTPException(404, "Results not ready yet")

    with open(output_path) as f:
        return json.load(f)


def _run_analysis(job_id: str, video_path: Path):
    """Run analysis in background."""
    try:
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["progress"] = 10

        pipeline = AnalysisPipeline(sample_rate=2)
        stats = pipeline.analyze(video_path)

        # Save results
        output_path = OUTPUT_DIR / f"{job_id}_stats.json"
        with open(output_path, "w") as f:
            json.dump(stats.model_dump(), f, indent=2)

        jobs[job_id]["status"] = "complete"
        jobs[job_id]["progress"] = 100
        jobs[job_id]["result"] = stats
        logger.info(f"Job {job_id} complete")

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
