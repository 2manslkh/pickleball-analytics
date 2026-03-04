"""Match statistics aggregation."""

import numpy as np
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pydantic import BaseModel

from src.analysis.shot_classifier import Shot, ShotType, ShotOutcome, Rally
from src.court.court_detector import KITCHEN_DEPTH, NET_POSITION


class PlayerStats(BaseModel):
    """Stats for a single player."""
    player_id: int
    team: int | None = None

    # Shot counts
    total_shots: int = 0
    dinks: int = 0
    drives: int = 0
    drops: int = 0
    lobs: int = 0
    volleys: int = 0
    overheads: int = 0
    serves: int = 0
    returns: int = 0

    # Accuracy / effectiveness
    dink_accuracy: float = 0.0       # % dinks that landed in kitchen
    third_shot_drop_attempts: int = 0
    third_shot_drop_success: float = 0.0  # % that resulted in winning the point or neutral
    serve_in_pct: float = 0.0

    # Errors
    unforced_errors: int = 0
    forced_errors: int = 0  # Opponent hit a winner
    winners: int = 0        # Unreturnable shots this player hit

    # Positioning
    kitchen_time_pct: float = 0.0      # % of time at kitchen line
    transition_time_pct: float = 0.0
    baseline_time_pct: float = 0.0
    avg_position: tuple[float, float] = (0.0, 0.0)

    # Averages
    avg_shot_speed: float = 0.0
    avg_rally_length: float = 0.0


class TeamStats(BaseModel):
    """Stats for a team (2 players in doubles)."""
    team_id: int
    players: list[PlayerStats] = []
    points_won: int = 0
    points_lost: int = 0
    side_out_pct: float = 0.0  # Points won when returning
    scoring_runs: list[int] = []  # Consecutive points won


class MatchStats(BaseModel):
    """Complete match statistics."""
    duration_seconds: float = 0.0
    total_points: int = 0
    total_rallies: int = 0
    avg_rally_length: float = 0.0
    longest_rally: int = 0

    teams: list[TeamStats] = []
    players: list[PlayerStats] = []
    rallies: list[dict] = []  # Serialized rally summaries

    # Shot distribution across match
    shot_distribution: dict[str, int] = {}

    # Momentum
    score_progression: list[dict] = []  # [{point: N, team0: X, team1: Y}]

    # LLM insights
    llm_observations: list[str] = []  # High-level observations from vision LLM


class StatsAggregator:
    """Aggregates shots and rallies into match statistics."""

    def __init__(self):
        self.rallies: list[Rally] = []
        self.player_shots: dict[int, list[Shot]] = defaultdict(list)
        self.player_zones: dict[int, list[str]] = defaultdict(list)
        self.player_teams: dict[int, int] = {}

    def add_rally(self, rally: Rally):
        """Add a completed rally."""
        self.rallies.append(rally)
        for shot in rally.shots:
            self.player_shots[shot.player_id].append(shot)
            if shot.team is not None:
                self.player_teams[shot.player_id] = shot.team

    def add_position_observation(self, player_id: int, zone: str):
        """Track where a player is standing."""
        self.player_zones[player_id].append(zone)

    def compute(self, fps: float = 30.0, total_frames: int = 0) -> MatchStats:
        """Compute all match statistics.

        Args:
            fps: Video frame rate.
            total_frames: Total frames in video.

        Returns:
            Complete MatchStats.
        """
        match = MatchStats()
        match.duration_seconds = total_frames / fps if fps > 0 else 0
        match.total_rallies = len(self.rallies)
        match.total_points = len(self.rallies)

        # Rally stats
        rally_lengths = [r.length for r in self.rallies]
        if rally_lengths:
            match.avg_rally_length = float(np.mean(rally_lengths))
            match.longest_rally = max(rally_lengths)

        # Global shot distribution
        all_shots = [s for shots in self.player_shots.values() for s in shots]
        match.shot_distribution = dict(Counter(s.shot_type.value for s in all_shots))

        # Player stats
        for pid, shots in self.player_shots.items():
            ps = self._compute_player_stats(pid, shots)
            match.players.append(ps)

        # Team stats
        teams: dict[int, list[PlayerStats]] = defaultdict(list)
        for ps in match.players:
            if ps.team is not None:
                teams[ps.team].append(ps)

        for team_id, players in teams.items():
            ts = self._compute_team_stats(team_id, players)
            match.teams.append(ts)

        # Score progression
        match.score_progression = self._compute_score_progression()

        # Rally summaries
        match.rallies = [
            {
                "number": i + 1,
                "length": r.length,
                "winner_team": r.point_winner_team,
                "ending": r.ending_type,
                "shots": [s.shot_type.value for s in r.shots],
            }
            for i, r in enumerate(self.rallies)
        ]

        return match

    def _compute_player_stats(self, player_id: int, shots: list[Shot]) -> PlayerStats:
        """Compute stats for a single player."""
        ps = PlayerStats(
            player_id=player_id,
            team=self.player_teams.get(player_id),
        )

        type_counts = Counter(s.shot_type for s in shots)
        ps.total_shots = len(shots)
        ps.dinks = type_counts.get(ShotType.DINK, 0)
        ps.drives = type_counts.get(ShotType.DRIVE, 0)
        ps.drops = type_counts.get(ShotType.DROP, 0)
        ps.lobs = type_counts.get(ShotType.LOB, 0)
        ps.volleys = type_counts.get(ShotType.VOLLEY, 0)
        ps.overheads = type_counts.get(ShotType.OVERHEAD, 0)
        ps.serves = type_counts.get(ShotType.SERVE, 0)
        ps.returns = type_counts.get(ShotType.RETURN, 0)

        # Dink accuracy (dinks that landed in kitchen)
        dink_shots = [s for s in shots if s.shot_type == ShotType.DINK]
        if dink_shots:
            in_kitchen = sum(
                1 for s in dink_shots
                if s.court_position and self._is_in_kitchen(s.court_position)
            )
            ps.dink_accuracy = in_kitchen / len(dink_shots) * 100

        # 3rd shot drops
        third_shots = [s for s in shots if s.is_third_shot and s.shot_type == ShotType.DROP]
        ps.third_shot_drop_attempts = len(third_shots)
        # Success = not an error
        if third_shots:
            successes = sum(1 for s in third_shots if s.outcome != ShotOutcome.ERROR)
            ps.third_shot_drop_success = successes / len(third_shots) * 100

        # Serves
        serve_shots = [s for s in shots if s.shot_type == ShotType.SERVE]
        if serve_shots:
            in_serves = sum(1 for s in serve_shots if s.outcome != ShotOutcome.OUT)
            ps.serve_in_pct = in_serves / len(serve_shots) * 100

        # Errors and winners
        ps.unforced_errors = sum(1 for s in shots if s.outcome == ShotOutcome.ERROR)
        ps.winners = sum(1 for s in shots if s.outcome == ShotOutcome.WINNER)

        # Average shot speed
        speeds = [s.ball_speed for s in shots if s.ball_speed > 0]
        if speeds:
            ps.avg_shot_speed = float(np.mean(speeds))

        # Positioning
        zones = self.player_zones.get(player_id, [])
        if zones:
            zone_counts = Counter(zones)
            total = len(zones)
            kitchen_zones = sum(v for k, v in zone_counts.items() if "kitchen" in k)
            transition_zones = sum(v for k, v in zone_counts.items() if "transition" in k)
            baseline_zones = sum(v for k, v in zone_counts.items() if "baseline" in k)

            ps.kitchen_time_pct = kitchen_zones / total * 100
            ps.transition_time_pct = transition_zones / total * 100
            ps.baseline_time_pct = baseline_zones / total * 100

        return ps

    def _compute_team_stats(self, team_id: int, players: list[PlayerStats]) -> TeamStats:
        """Compute team-level stats."""
        ts = TeamStats(team_id=team_id, players=players)

        for rally in self.rallies:
            if rally.point_winner_team == team_id:
                ts.points_won += 1
            elif rally.point_winner_team is not None:
                ts.points_lost += 1

        return ts

    def _compute_score_progression(self) -> list[dict]:
        """Build score progression over time."""
        progression = []
        scores = {0: 0, 1: 0}

        for i, rally in enumerate(self.rallies):
            if rally.point_winner_team is not None:
                scores[rally.point_winner_team] += 1
            progression.append({
                "point": i + 1,
                "team_0": scores[0],
                "team_1": scores[1],
            })

        return progression

    @staticmethod
    def _is_in_kitchen(court_pos: tuple[float, float]) -> bool:
        """Check if court position is in the kitchen."""
        _, y = court_pos
        return (NET_POSITION - KITCHEN_DEPTH <= y <= NET_POSITION + KITCHEN_DEPTH)
