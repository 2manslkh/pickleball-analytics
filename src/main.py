"""CLI entry point for pickleball analytics."""

import json
import typer
from pathlib import Path
from loguru import logger

from src.pipeline import AnalysisPipeline

app = typer.Typer(help="🏓 Pickleball Match Analytics")


@app.command()
def analyze(
    video: Path = typer.Argument(..., help="Path to match video file"),
    output: Path = typer.Option(None, "--output", "-o", help="Output JSON path"),
    model: str = typer.Option("yolov8n.pt", "--model", "-m", help="YOLO model path"),
    confidence: float = typer.Option(0.5, "--confidence", "-c", help="Detection confidence"),
    sample_rate: int = typer.Option(2, "--sample-rate", "-s", help="Process every Nth frame"),
):
    """Analyze a pickleball match video and generate stats."""

    logger.info(f"Starting analysis of {video}")

    pipeline = AnalysisPipeline(
        player_model=model,
        player_confidence=confidence,
        sample_rate=sample_rate,
    )

    stats = pipeline.analyze(video)

    # Default output path
    if output is None:
        output = Path("data/outputs") / f"{video.stem}_stats.json"
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
    print("🏓 MATCH ANALYSIS REPORT")
    print("=" * 60)
    print(f"Duration: {stats.duration_seconds:.0f}s")
    print(f"Total Rallies: {stats.total_rallies}")
    print(f"Avg Rally Length: {stats.avg_rally_length:.1f} shots")
    print(f"Longest Rally: {stats.longest_rally} shots")

    print("\n📊 Shot Distribution:")
    for shot_type, count in sorted(stats.shot_distribution.items(), key=lambda x: -x[1]):
        print(f"  {shot_type:<12} {count:>4}")

    for player in stats.players:
        print(f"\n{'─' * 60}")
        print(f"👤 Player {player.player_id} (Team {'Near' if player.team == 0 else 'Far' if player.team is not None else '?'})")
        print(f"  Total Shots: {player.total_shots}")
        print(f"  Dinks: {player.dinks}  (accuracy: {player.dink_accuracy:.0f}%)")
        print(f"  Drives: {player.drives}")
        print(f"  Drops: {player.drops}  (3rd shot attempts: {player.third_shot_drop_attempts})")
        print(f"  Lobs: {player.lobs}")
        print(f"  Volleys: {player.volleys}")
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
            print(f"  Team {team.team_id}: {team.points_won} pts won, {team.points_lost} lost")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    app()
