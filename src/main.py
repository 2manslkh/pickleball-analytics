"""CLI entry point for pickleball analytics."""

import json
import typer
from pathlib import Path
from loguru import logger

from src.pipeline import AnalysisPipeline
from src.downloader import is_youtube_url, download_youtube

app = typer.Typer(help="🏓 Pickleball Match Analytics — Hybrid CV + LLM")


@app.command()
def analyze(
    video: str = typer.Argument(..., help="Path to match video file or YouTube URL"),
    output: Path = typer.Option(None, "--output", "-o", help="Output JSON path"),
    model: str = typer.Option("yolov8n.pt", "--model", "-m", help="YOLO model path"),
    confidence: float = typer.Option(0.5, "--confidence", "-c", help="Detection confidence"),
    sample_rate: int = typer.Option(2, "--sample-rate", "-s", help="Process every Nth frame"),
    llm: str = typer.Option("gemini", "--llm", help="LLM provider: gemini or openai"),
    llm_model: str = typer.Option(None, "--llm-model", help="LLM model name override"),
    batch_seconds: float = typer.Option(10.0, "--batch-sec", help="Seconds per LLM batch"),
):
    """Analyze a pickleball match video and generate stats.

    Uses YOLO for player/ball detection, ByteTrack for tracking,
    and a vision LLM (Gemini/GPT-4o) for shot classification.
    """

    # Handle YouTube URLs
    if is_youtube_url(video):
        logger.info(f"Downloading YouTube video: {video}")
        video_path = download_youtube(video)
    else:
        video_path = Path(video)

    logger.info(f"Starting hybrid analysis of {video_path}")

    pipeline = AnalysisPipeline(
        player_model=model,
        player_confidence=confidence,
        sample_rate=sample_rate,
        llm_provider=llm,
        llm_model=llm_model,
        llm_batch_seconds=batch_seconds,
    )

    stats = pipeline.analyze(video_path)

    # Default output path
    if output is None:
        output = Path("data/outputs") / f"{video_path.stem}_stats.json"
        output.parent.mkdir(parents=True, exist_ok=True)

    # Write results
    with open(output, "w") as f:
        json.dump(stats.model_dump(), f, indent=2)

    logger.info(f"Stats written to {output}")

    # Print summary
    _print_summary(stats)


def _print_summary(stats):
    """Print a human-readable summary to console."""
    print("\n" + "=" * 60)
    print("🏓 MATCH ANALYSIS REPORT (Hybrid CV + LLM)")
    print("=" * 60)
    print(f"Duration: {stats.duration_seconds:.0f}s")
    print(f"Total Rallies: {stats.total_rallies}")
    print(f"Avg Rally Length: {stats.avg_rally_length:.1f} shots")
    print(f"Longest Rally: {stats.longest_rally} shots")

    print("\n📊 Shot Distribution:")
    for shot_type, count in sorted(stats.shot_distribution.items(), key=lambda x: -x[1]):
        print(f"  {shot_type:<12} {count:>4}")

    for player in stats.players:
        team_label = "Near" if player.team == 0 else "Far" if player.team is not None else "?"
        print(f"\n{'─' * 60}")
        print(f"👤 Player {player.player_id} (Team {team_label})")
        print(f"  Total Shots: {player.total_shots}")
        print(f"  Dinks: {player.dinks}  (accuracy: {player.dink_accuracy:.0f}%)")
        print(f"  Drives: {player.drives}")
        print(f"  Drops: {player.drops}  (3rd shot attempts: {player.third_shot_drop_attempts})")
        print(f"  Lobs: {player.lobs}")
        print(f"  Volleys: {player.volleys}")
        print(f"  Overheads: {player.overheads}")
        print(f"  Serves: {player.serves}")
        print(f"  Unforced Errors: {player.unforced_errors}")
        print(f"  Winners: {player.winners}")
        print(f"  Court Position: Kitchen {player.kitchen_time_pct:.0f}% | "
              f"Transition {player.transition_time_pct:.0f}% | "
              f"Baseline {player.baseline_time_pct:.0f}%")

    if stats.teams:
        print(f"\n{'─' * 60}")
        print("🏆 Team Scores:")
        for team in stats.teams:
            label = "Near" if team.team_id == 0 else "Far"
            print(f"  Team {label}: {team.points_won} pts won, {team.points_lost} lost")

    # LLM observations
    if hasattr(stats, 'llm_observations') and stats.llm_observations:
        print(f"\n{'─' * 60}")
        print("🧠 AI Observations:")
        for obs in stats.llm_observations:
            print(f"  • {obs}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    app()
