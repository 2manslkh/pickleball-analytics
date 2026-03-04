"""Modal deployment for Pickleball Analytics API.

Deploy: modal deploy modal_app.py
Dev:    modal serve modal_app.py
"""

import modal
import json
import uuid
import asyncio
from pathlib import Path

# ── Modal Config ──────────────────────────────────────────────

app = modal.App("pickleball-analytics")

# Container image with all dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg", "libgl1-mesa-glx", "libglib2.0-0")
    .pip_install(
        # CV
        "ultralytics>=8.1.0",
        "opencv-python-headless>=4.9.0",
        "numpy>=1.26.0",
        "supervision>=0.19.0",
        # LLM
        "google-generativeai>=0.8.0",
        "openai>=1.12.0",
        # YouTube
        "yt-dlp>=2024.1.0",
        # API / Utils
        "fastapi>=0.109.0",
        "pydantic>=2.5.0",
        "loguru>=0.7.0",
        "tqdm>=4.66.0",
        "pandas>=2.2.0",
        "python-multipart>=0.0.6",
    )
    # Pre-download YOLO model into the image
    .run_commands("python -c \"from ultralytics import YOLO; YOLO('yolov8n.pt')\"")
)

# Persistent volume for cached videos and results
volume = modal.Volume.from_name("pickleball-data", create_if_missing=True)
VOLUME_PATH = "/data"
VIDEOS_DIR = f"{VOLUME_PATH}/videos"
RESULTS_DIR = f"{VOLUME_PATH}/results"

# Secrets
secrets = [modal.Secret.from_name("pickleball-secrets", required_keys=[])]


# ── GPU Analysis Function ────────────────────────────────────

@app.function(
    image=image,
    gpu="T4",
    timeout=600,
    volumes={VOLUME_PATH: volume},
    secrets=secrets,
)
def run_cv_pass(video_path: str, sample_rate: int = 2, max_seconds: float = 0) -> dict:
    """Run CV detection + tracking on GPU. Returns tracking data as serializable dict."""
    import cv2
    import numpy as np
    from src.detection.player_detector import PlayerDetector
    from src.detection.ball_detector import BallDetector
    from src.tracking.tracker import MultiObjectTracker
    from src.court.court_detector import CourtDetector
    from loguru import logger
    from tqdm import tqdm

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Cap frames if max_seconds set
    if max_seconds > 0:
        max_frames = int(max_seconds * fps)
        total_frames = min(total_frames, max_frames)
        logger.info(f"CV Pass: {width}x{height} @ {fps:.1f}fps, capped to {total_frames} frames ({max_seconds}s)")
    else:
        logger.info(f"CV Pass: {width}x{height} @ {fps:.1f}fps, {total_frames} frames")

    player_detector = PlayerDetector("yolov8n.pt", confidence=0.5)
    ball_detector = BallDetector("yolov8n.pt", confidence=0.3)
    tracker = MultiObjectTracker()
    court_detector = CourtDetector()

    court_mapping = None
    zone_observations: dict[int, list[str]] = {}

    # For LLM: collect annotated frames as JPEG bytes
    llm_frames: list[bytes] = []
    llm_frame_indices: list[int] = []
    llm_annotations: list[dict] = []

    # Sample rate for LLM frames (every ~0.5s of video)
    llm_sample_interval = max(1, int(fps * 0.5))

    frame_idx = 0
    pbar = tqdm(total=total_frames, desc="CV Pass (GPU)", unit="frame")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if max_seconds > 0 and frame_idx >= total_frames:
            break

        if frame_idx % sample_rate == 0:
            # Court detection (first 3 seconds)
            if court_mapping is None or frame_idx < int(fps * 3):
                court_mapping = court_detector.detect(frame)

            # Resize for faster inference (YOLO handles this internally but let's be explicit)
            raw_detections = player_detector.detect(frame)
            players = player_detector.filter_players(raw_detections)
            ball = ball_detector.detect(frame)

            tracker.update_players(players, frame_idx)
            tracker.update_ball(ball.center if ball else None, frame_idx)

            # Zone tracking
            if court_mapping:
                for player in tracker.get_active_players():
                    if player.last_position:
                        try:
                            court_pos = court_mapping.image_to_court(player.last_position)
                            zone = court_mapping.get_zone(court_pos)
                            if player.tracker_id not in zone_observations:
                                zone_observations[player.tracker_id] = []
                            zone_observations[player.tracker_id].append(zone)
                        except Exception:
                            pass

            # Collect frames for LLM
            if frame_idx % llm_sample_interval == 0:
                # Annotate frame
                annotated = frame.copy()
                team_colors = {0: (0, 255, 0), 1: (255, 0, 0)}
                active_players = tracker.get_active_players()

                annotation = {"players": [], "ball": None}
                for p in active_players:
                    if p.detections:
                        bbox = p.detections[-1].bbox
                        color = team_colors.get(p.team, (255, 255, 255))
                        x1, y1, x2, y2 = [int(v) for v in bbox]
                        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                        cv2.putText(annotated, f"P{p.tracker_id}", (x1, y1 - 5),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                        annotation["players"].append({
                            "bbox": bbox.tolist(), "id": p.tracker_id, "team": p.team
                        })

                if ball:
                    cx, cy = int(ball.center[0]), int(ball.center[1])
                    cv2.circle(annotated, (cx, cy), max(int(ball.radius), 5), (0, 255, 255), 2)
                    annotation["ball"] = {"center": ball.center, "radius": ball.radius}

                # Encode as JPEG bytes
                _, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 75])
                llm_frames.append(buf.tobytes())
                llm_frame_indices.append(frame_idx)
                llm_annotations.append(annotation)

        frame_idx += 1
        pbar.update(1)

    pbar.close()
    cap.release()

    # Assign teams
    if court_mapping:
        try:
            midline_img = court_mapping.court_to_image((10, 22))
            tracker.assign_teams(midline_img[1])
        except Exception:
            tracker.assign_teams()
    else:
        tracker.assign_teams()

    # Serialize tracker data
    player_data = {}
    for pid, player in tracker.players.items():
        player_data[str(pid)] = {
            "tracker_id": player.tracker_id,
            "team": player.team,
            "positions": player.positions[-200:],  # Keep recent positions
        }

    ball_data = {
        "positions": tracker.ball.positions[-500:],
        "velocities": tracker.ball.velocities[-500:],
        "frame_indices": tracker.ball.frame_indices[-500:],
    }

    logger.info(
        f"CV Pass complete: {len(player_data)} players tracked, "
        f"{len(llm_frames)} frames for LLM"
    )

    return {
        "fps": fps,
        "total_frames": frame_idx,
        "player_data": player_data,
        "ball_data": ball_data,
        "zone_observations": zone_observations,
        "llm_frames": llm_frames,
        "llm_frame_indices": llm_frame_indices,
        "llm_annotations": llm_annotations,
    }


# ── LLM Analysis Function (CPU, parallel) ────────────────────

@app.function(
    image=image,
    timeout=300,
    secrets=secrets,
)
def run_llm_batch(
    frames_jpeg: list[bytes],
    frame_indices: list[int],
    provider: str = "gemini",
    model: str | None = None,
) -> dict:
    """Analyze a single batch of frames with vision LLM. Runs on CPU."""
    import base64
    import os
    from loguru import logger

    PROMPT = """You are an expert pickleball analyst watching a doubles match.

Analyze these annotated frames (players have colored boxes, ball is marked yellow).

Identify shot events and rally structure:

For each shot:
- shot_type: serve, return, dink, drive, drop, lob, volley, overhead
- player_position: near_left, near_right, far_left, far_right
- outcome: in, out, net, winner, error, returned
- confidence: high, medium, low

Respond in JSON:
```json
{
  "rallies": [{
    "shots": [{"frame_range": [0,30], "shot_type": "serve", "player_position": "near_right", "outcome": "in", "confidence": "high", "notes": ""}],
    "rally_length": 5,
    "point_winner": "near_team",
    "ending_type": "unforced_error",
    "key_moment": "description"
  }],
  "observations": ["insight about player tendencies"]
}
```"""

    encoded = [base64.b64encode(f).decode("utf-8") for f in frames_jpeg]

    try:
        if provider == "gemini":
            import google.generativeai as genai
            api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
            genai.configure(api_key=api_key)
            gmodel = genai.GenerativeModel(model or "gemini-2.5-flash")

            parts = [PROMPT, f"\nFrames {frame_indices[0]}-{frame_indices[-1]}:\n"]
            for b64 in encoded:
                parts.append({"mime_type": "image/jpeg", "data": base64.b64decode(b64)})

            response = gmodel.generate_content(parts)
            text = response.text

        elif provider == "openai":
            import openai
            client = openai.OpenAI()
            content = [{"type": "text", "text": PROMPT + f"\nFrames {frame_indices[0]}-{frame_indices[-1]}:\n"}]
            for b64 in encoded:
                content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "high"}})

            response = client.chat.completions.create(
                model=model or "gpt-4o",
                messages=[{"role": "user", "content": content}],
                max_tokens=4096,
                response_format={"type": "json_object"},
            )
            text = response.choices[0].message.content
        else:
            return {"rallies": [], "observations": []}

        # Parse JSON
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        if text.endswith("```"):
            text = text[:-3]

        return json.loads(text.strip())

    except Exception as e:
        logger.error(f"LLM batch failed: {e}")
        return {"rallies": [], "observations": []}


# ── YouTube Download Function ─────────────────────────────────

@app.function(
    image=image,
    timeout=300,
    volumes={VOLUME_PATH: volume},
)
def download_video(url: str) -> dict:
    """Download YouTube video to volume. Returns path and metadata."""
    import subprocess
    import re
    from loguru import logger

    patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?youtu\.be/([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
    ]
    video_id = None
    for p in patterns:
        m = re.match(p, url.strip())
        if m:
            video_id = m.group(1)
            break

    if not video_id:
        raise ValueError(f"Invalid YouTube URL: {url}")

    video_dir = Path(VIDEOS_DIR)
    video_dir.mkdir(parents=True, exist_ok=True)

    # Check cache
    cached = video_dir / f"{video_id}.mp4"
    if cached.exists():
        logger.info(f"Cache hit: {cached}")
        volume.commit()
        return {"path": str(cached), "video_id": video_id, "cached": True}

    # Download
    output_template = str(video_dir / f"{video_id}.%(ext)s")
    cmd = [
        "yt-dlp",
        "--format", "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "--merge-output-format", "mp4",
        "--output", output_template,
        "--no-playlist",
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {result.stderr[:500]}")

    # Find file
    for ext in ["mp4", "mkv", "webm"]:
        f = video_dir / f"{video_id}.{ext}"
        if f.exists():
            logger.info(f"Downloaded: {f} ({f.stat().st_size / 1024 / 1024:.1f}MB)")
            volume.commit()
            return {"path": str(f), "video_id": video_id, "cached": False}

    raise RuntimeError("Download completed but file not found")


# ── Stats Computation (CPU) ───────────────────────────────────

@app.function(image=image, timeout=120)
def compute_stats(
    cv_data: dict,
    llm_results: list[dict],
    mode: str = "hybrid",
) -> dict:
    """Merge CV + LLM data into final match stats."""
    import numpy as np
    from collections import Counter, defaultdict
    from src.analysis.stats import StatsAggregator, MatchStats
    from src.analysis.shot_classifier import Shot, ShotType, ShotOutcome, Rally

    stats = StatsAggregator()
    fps = cv_data["fps"]
    total_frames = cv_data["total_frames"]
    player_data = cv_data["player_data"]

    # Set player teams
    for pid_str, pdata in player_data.items():
        pid = int(pid_str)
        if pdata["team"] is not None:
            stats.player_teams[pid] = pdata["team"]

    # Zone observations
    for pid_str, zones in cv_data["zone_observations"].items():
        pid = int(pid_str)
        for zone in zones:
            stats.add_position_observation(pid, zone)

    if mode == "hybrid" and llm_results:
        # Map positions to player IDs
        near_players = sorted(
            [(int(k), v) for k, v in player_data.items() if v["team"] == 0],
            key=lambda x: np.mean([p[0] for p in x[1]["positions"][-50:]]) if x[1]["positions"] else 0,
        )
        far_players = sorted(
            [(int(k), v) for k, v in player_data.items() if v["team"] == 1],
            key=lambda x: np.mean([p[0] for p in x[1]["positions"][-50:]]) if x[1]["positions"] else 0,
        )

        pos_map = {}
        if len(near_players) >= 1: pos_map["near_left"] = near_players[0][0]
        if len(near_players) >= 2: pos_map["near_right"] = near_players[1][0]
        if len(far_players) >= 1: pos_map["far_left"] = far_players[0][0]
        if len(far_players) >= 2: pos_map["far_right"] = far_players[1][0]

        for batch_result in llm_results:
            for rally_data in batch_result.get("rallies", []):
                shots = []
                for s in rally_data.get("shots", []):
                    try:
                        shot_type = ShotType(s.get("shot_type", "unknown"))
                    except ValueError:
                        shot_type = ShotType.UNKNOWN
                    try:
                        outcome = ShotOutcome(s.get("outcome", "unknown"))
                    except ValueError:
                        outcome = ShotOutcome.UNKNOWN

                    pid = pos_map.get(s.get("player_position", ""), -1)
                    team = player_data.get(str(pid), {}).get("team") if pid >= 0 else None

                    shots.append(Shot(
                        frame_idx=s.get("frame_range", [0, 0])[0],
                        shot_type=shot_type,
                        outcome=outcome,
                        player_id=pid,
                        team=team,
                        ball_speed=0,
                        ball_position=(0, 0),
                        court_position=None,
                        is_third_shot=(len(shots) == 2 and shot_type == ShotType.DROP),
                    ))

                winner = None
                pw = rally_data.get("point_winner")
                if pw == "near_team": winner = 0
                elif pw == "far_team": winner = 1

                rally = Rally(
                    shots=shots,
                    point_winner_team=winner,
                    ending_type=rally_data.get("ending_type"),
                )
                stats.add_rally(rally)

    else:
        # CV-only: use ball velocity for shot detection
        ball = cv_data["ball_data"]
        velocities = ball["velocities"]
        positions = ball["positions"]
        frame_indices = ball["frame_indices"]

        from src.analysis.shot_classifier import ShotClassifier
        classifier = ShotClassifier()
        rally_active = False
        frames_since_hit = 0

        for i in range(2, len(velocities)):
            vx, vy = velocities[i]
            pvx, pvy = velocities[i - 1]

            vx_flip = np.sign(vx) != np.sign(pvx) and abs(vx) > 1.0
            vy_flip = np.sign(vy) != np.sign(pvy) and abs(vy) > 1.0
            speed_spike = (np.sqrt(vx**2 + vy**2) > np.sqrt(pvx**2 + pvy**2) * 1.5)

            if not (vx_flip or vy_flip or speed_spike):
                frames_since_hit += 1
                if rally_active and frames_since_hit > 90:
                    rally = classifier.end_rally()
                    if rally.shots:
                        stats.add_rally(rally)
                    rally_active = False
                continue

            if frames_since_hit < 5:
                continue
            frames_since_hit = 0

            if not rally_active:
                rally_active = True
                classifier.new_rally()

            # Find closest player
            bp = positions[i]
            closest_pid = -1
            min_dist = float("inf")
            for pid_str, pdata in player_data.items():
                if pdata["positions"]:
                    pp = pdata["positions"][-1]
                    d = np.sqrt((pp[0] - bp[0])**2 + (pp[1] - bp[1])**2)
                    if d < min_dist:
                        min_dist = d
                        closest_pid = int(pid_str)

            if closest_pid < 0 or min_dist > 200:
                continue

            player_pos = player_data.get(str(closest_pid), {}).get("positions", [(0, 0)])[-1]
            classifier.classify(
                ball_positions=positions[max(0, i - 10):i + 1],
                ball_velocities=velocities[max(0, i - 10):i + 1],
                hitting_player_id=closest_pid,
                hitting_player_team=player_data.get(str(closest_pid), {}).get("team"),
                hitting_player_pos=player_pos,
                frame_idx=frame_indices[i],
            )

        if rally_active:
            rally = classifier.end_rally()
            if rally.shots:
                stats.add_rally(rally)

    match_stats = stats.compute(fps=fps, total_frames=total_frames)

    # Add LLM observations
    if mode == "hybrid" and llm_results:
        all_obs = []
        for r in llm_results:
            all_obs.extend(r.get("observations", []))
        match_stats.llm_observations = all_obs

    return match_stats.model_dump()


# ── Web API ───────────────────────────────────────────────────

@app.function(
    image=image,
    timeout=60,
    volumes={VOLUME_PATH: volume},
)
@modal.concurrent(max_inputs=20)
@modal.asgi_app()
def web():
    """FastAPI web server."""
    from fastapi import FastAPI, UploadFile, File, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse, Response
    from pydantic import BaseModel

    api = FastAPI(title="🏓 Pickleball Analytics API")

    api.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    class AnalyzeRequest(BaseModel):
        url: str | None = None
        mode: str = "hybrid"  # "cv" or "hybrid"
        llm_provider: str = "gemini"
        max_seconds: float = 0  # 0 = full video, >0 = cap at N seconds

    @api.post("/analyze")
    async def analyze_video(req: AnalyzeRequest):
        """Full analysis pipeline. Accepts YouTube URL or file upload."""
        if not req.url:
            raise HTTPException(400, "Provide a YouTube URL")

        try:
            # Step 1: Download
            dl_result = download_video.remote(req.url)
            video_path = dl_result["path"]

            # Step 2: CV Pass (GPU)
            cv_data = run_cv_pass.remote(video_path, sample_rate=2, max_seconds=req.max_seconds)

            # Step 3: LLM Pass (parallel batches)
            llm_results = []
            if req.mode == "hybrid":
                frames = cv_data["llm_frames"]
                indices = cv_data["llm_frame_indices"]
                batch_size = 16

                # Launch all batches in parallel
                futures = []
                for i in range(0, len(frames), batch_size):
                    batch_frames = frames[i:i + batch_size]
                    batch_indices = indices[i:i + batch_size]
                    futures.append(
                        run_llm_batch.spawn(
                            batch_frames, batch_indices,
                            provider=req.llm_provider,
                        )
                    )

                # Collect results
                llm_results = [f.get() for f in futures]

            # Step 4: Compute stats
            # Remove large frame data before sending to stats function
            cv_data_light = {k: v for k, v in cv_data.items()
                           if k not in ("llm_frames", "llm_annotations")}
            result = compute_stats.remote(cv_data_light, llm_results, mode=req.mode)

            return result

        except Exception as e:
            raise HTTPException(500, str(e))

    @api.post("/analyze/upload")
    async def analyze_upload(
        video: UploadFile = File(...),
        mode: str = "hybrid",
        max_seconds: float = 0,
    ):
        """Upload a video file for analysis."""
        video_dir = Path(VIDEOS_DIR)
        video_dir.mkdir(parents=True, exist_ok=True)

        job_id = str(uuid.uuid4())[:8]
        ext = Path(video.filename or "video.mp4").suffix
        video_path = video_dir / f"{job_id}{ext}"

        content = await video.read()
        with open(video_path, "wb") as f:
            f.write(content)
        volume.commit()

        # Run same pipeline
        cv_data = run_cv_pass.remote(str(video_path), sample_rate=2, max_seconds=max_seconds)

        llm_results = []
        if mode == "hybrid":
            frames = cv_data["llm_frames"]
            indices = cv_data["llm_frame_indices"]
            batch_size = 16
            futures = []
            for i in range(0, len(frames), batch_size):
                futures.append(
                    run_llm_batch.spawn(
                        frames[i:i + batch_size],
                        indices[i:i + batch_size],
                    )
                )
            llm_results = [f.get() for f in futures]

        cv_data_light = {k: v for k, v in cv_data.items()
                        if k not in ("llm_frames", "llm_annotations")}
        result = compute_stats.remote(cv_data_light, llm_results, mode=mode)

        return result

    @api.get("/health")
    async def health():
        return {"status": "ok", "gpu": "T4"}

    return api
