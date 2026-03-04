"""Multi-object tracking using supervision's ByteTrack."""

import numpy as np
import supervision as sv
from dataclasses import dataclass, field
from loguru import logger

from src.detection.player_detector import Detection


@dataclass
class TrackedPlayer:
    """A player with a persistent ID across frames."""
    tracker_id: int
    team: int | None = None  # 0 or 1 (assigned by team classifier)
    positions: list[tuple[float, float]] = field(default_factory=list)
    detections: list[Detection] = field(default_factory=list)
    frame_indices: list[int] = field(default_factory=list)

    @property
    def last_position(self) -> tuple[float, float] | None:
        return self.positions[-1] if self.positions else None

    def add_observation(self, detection: Detection, frame_idx: int):
        self.positions.append(detection.bottom_center)
        self.detections.append(detection)
        self.frame_indices.append(frame_idx)


@dataclass
class BallTrack:
    """Ball trajectory across frames."""
    positions: list[tuple[float, float]] = field(default_factory=list)
    frame_indices: list[int] = field(default_factory=list)
    velocities: list[tuple[float, float]] = field(default_factory=list)

    def add_observation(self, pos: tuple[float, float], frame_idx: int):
        if self.positions:
            dt = frame_idx - self.frame_indices[-1]
            if dt > 0:
                vx = (pos[0] - self.positions[-1][0]) / dt
                vy = (pos[1] - self.positions[-1][1]) / dt
                self.velocities.append((vx, vy))
            else:
                self.velocities.append((0.0, 0.0))
        else:
            self.velocities.append((0.0, 0.0))

        self.positions.append(pos)
        self.frame_indices.append(frame_idx)

    @property
    def speed_at(self) -> list[float]:
        """Speed magnitude at each observation."""
        return [np.sqrt(vx**2 + vy**2) for vx, vy in self.velocities]


class MultiObjectTracker:
    """Tracks players and ball across video frames.

    Uses ByteTrack for player tracking (handles occlusion well)
    and simple nearest-neighbor for ball (single object).
    """

    def __init__(self):
        self.byte_tracker = sv.ByteTrack(
            track_activation_threshold=0.4,
            lost_track_buffer=30,  # Keep tracks alive for 30 frames
            minimum_matching_threshold=0.8,
            frame_rate=30,
        )
        self.players: dict[int, TrackedPlayer] = {}
        self.ball = BallTrack()
        self.frame_count = 0
        logger.info("MultiObjectTracker initialized")

    def update_players(self, detections: list[Detection], frame_idx: int):
        """Update player tracks with new detections.

        Args:
            detections: Player detections for current frame.
            frame_idx: Current frame index.
        """
        if not detections:
            self.frame_count = frame_idx
            return

        # Convert to supervision Detections format
        bboxes = np.array([d.bbox for d in detections])
        confidences = np.array([d.confidence for d in detections])

        sv_detections = sv.Detections(
            xyxy=bboxes,
            confidence=confidences,
        )

        # Run ByteTrack
        tracked = self.byte_tracker.update_with_detections(sv_detections)

        if tracked.tracker_id is None:
            return

        # Update our player records
        for i, tracker_id in enumerate(tracked.tracker_id):
            tid = int(tracker_id)

            if tid not in self.players:
                self.players[tid] = TrackedPlayer(tracker_id=tid)
                logger.debug(f"New player track: {tid}")

            # Reconstruct Detection from tracked bbox
            det = Detection(
                bbox=tracked.xyxy[i],
                confidence=float(tracked.confidence[i]) if tracked.confidence is not None else 0.5,
                class_id=0,
            )
            self.players[tid].add_observation(det, frame_idx)

        self.frame_count = frame_idx

    def update_ball(self, ball_pos: tuple[float, float] | None, frame_idx: int):
        """Update ball track.

        Args:
            ball_pos: Ball center position, or None if not detected.
            frame_idx: Current frame index.
        """
        if ball_pos is not None:
            self.ball.add_observation(ball_pos, frame_idx)

    def get_active_players(self, max_gap: int = 60) -> list[TrackedPlayer]:
        """Get players that were recently tracked.

        Args:
            max_gap: Max frames since last detection to still be considered active.

        Returns:
            List of active TrackedPlayer objects.
        """
        active = []
        for player in self.players.values():
            if player.frame_indices and (self.frame_count - player.frame_indices[-1]) <= max_gap:
                active.append(player)
        return active

    def assign_teams(self, court_midline_y: float | None = None):
        """Assign players to teams (team 0 = near side, team 1 = far side).

        Uses average Y position relative to court midline.
        If no midline provided, uses frame center.
        """
        active = self.get_active_players()
        if len(active) < 2:
            return

        # Compute average Y for each player
        avg_y = {}
        for player in active:
            if player.positions:
                avg_y[player.tracker_id] = np.mean([p[1] for p in player.positions[-100:]])

        if not avg_y:
            return

        midline = court_midline_y if court_midline_y else np.median(list(avg_y.values()))

        for player in active:
            if player.tracker_id in avg_y:
                player.team = 0 if avg_y[player.tracker_id] > midline else 1

        team_0 = [p for p in active if p.team == 0]
        team_1 = [p for p in active if p.team == 1]
        logger.info(f"Teams assigned: Near={len(team_0)}, Far={len(team_1)}")
