"""YouTube video downloader using yt-dlp."""

import re
import subprocess
from pathlib import Path
from loguru import logger


YOUTUBE_PATTERNS = [
    r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
    r'(?:https?://)?youtu\.be/([a-zA-Z0-9_-]{11})',
    r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
    r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
]


def is_youtube_url(url: str) -> bool:
    """Check if a URL is a valid YouTube link."""
    return any(re.match(p, url.strip()) for p in YOUTUBE_PATTERNS)


def extract_video_id(url: str) -> str | None:
    """Extract YouTube video ID from URL."""
    for pattern in YOUTUBE_PATTERNS:
        match = re.match(pattern, url.strip())
        if match:
            return match.group(1)
    return None


def download_youtube(
    url: str,
    output_dir: str | Path = "data/videos",
    max_resolution: int = 720,
) -> Path:
    """Download a YouTube video using yt-dlp.

    Args:
        url: YouTube URL.
        output_dir: Directory to save the video.
        max_resolution: Max vertical resolution (720p default — good balance of quality vs file size).

    Returns:
        Path to downloaded video file.

    Raises:
        RuntimeError: If download fails.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError(f"Could not extract video ID from: {url}")

    output_template = str(output_dir / f"{video_id}.%(ext)s")

    # Check if already downloaded
    for ext in ["mp4", "mkv", "webm"]:
        existing = output_dir / f"{video_id}.{ext}"
        if existing.exists():
            logger.info(f"Video already downloaded: {existing}")
            return existing

    logger.info(f"Downloading YouTube video: {video_id}")

    cmd = [
        "yt-dlp",
        "--format", f"bestvideo[height<={max_resolution}]+bestaudio/best[height<={max_resolution}]",
        "--merge-output-format", "mp4",
        "--output", output_template,
        "--no-playlist",
        "--no-overwrites",
        url,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 min timeout
        )
        if result.returncode != 0:
            raise RuntimeError(f"yt-dlp failed: {result.stderr}")
    except FileNotFoundError:
        raise RuntimeError(
            "yt-dlp not found. Install it: pip install yt-dlp"
        )

    # Find the downloaded file
    for ext in ["mp4", "mkv", "webm"]:
        downloaded = output_dir / f"{video_id}.{ext}"
        if downloaded.exists():
            logger.info(f"Downloaded: {downloaded} ({downloaded.stat().st_size / 1024 / 1024:.1f}MB)")
            return downloaded

    raise RuntimeError(f"Download completed but file not found in {output_dir}")


def get_video_info(url: str) -> dict:
    """Get video metadata without downloading.

    Returns:
        Dict with title, duration, thumbnail, etc.
    """
    cmd = [
        "yt-dlp",
        "--dump-json",
        "--no-playlist",
        url,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise RuntimeError(f"yt-dlp failed: {result.stderr}")

        import json
        info = json.loads(result.stdout)
        return {
            "id": info.get("id"),
            "title": info.get("title"),
            "duration": info.get("duration"),
            "thumbnail": info.get("thumbnail"),
            "uploader": info.get("uploader"),
            "view_count": info.get("view_count"),
        }
    except FileNotFoundError:
        raise RuntimeError("yt-dlp not found. Install it: pip install yt-dlp")
