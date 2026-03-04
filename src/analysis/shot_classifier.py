"""Shot classification based on ball trajectory and player positions."""

import numpy as np
from enum import Enum
from dataclasses import dataclass
from loguru import logger

from src.court.court_detector import (
    CourtMapping, NET_POSITION, KITCHEN_DEPTH, COURT_WIDTH, COURT_LENGTH,
)


class ShotType(str, Enum):
    SERVE = "serve"
    RETURN = "return"
    DINK = "dink"
    DRIVE = "drive"
    DROP = "drop"          # 3rd shot drop
    LOB = "lob"
    VOLLEY = "volley"
    OVERHEAD = "overhead"  # Smash/overhead
    ERNE = "erne"          # Volley around the kitchen (player outside sideline)
    ATP = "atp"            # Around the post shot
    RESET = "reset"        # Soft defensive shot to neutralize and get to kitchen
    SPEEDUP = "speedup"    # Sudden hard shot during a dink rally
    PASSING = "passing"    # Fast shot aimed to pass opponent at the net
    POACH = "poach"        # Player crosses to partner's side to intercept
    UNKNOWN = "unknown"


class ShotOutcome(str, Enum):
    IN = "in"              # Ball landed in bounds
    OUT = "out"            # Ball landed out
    NET = "net"            # Hit the net
    WINNER = "winner"      # Unreturnable shot
    ERROR = "error"        # Unforced error
    RETURNED = "returned"  # Opponent returned it
    UNKNOWN = "unknown"


@dataclass
class Shot:
    """A classified shot event."""
    frame_idx: int
    shot_type: ShotType
    outcome: ShotOutcome
    player_id: int  # Tracker ID of the hitting player
    team: int | None  # 0 or 1
    ball_speed: float  # Pixels per frame
    ball_position: tuple[float, float]  # Image coordinates
    court_position: tuple[float, float] | None  # Court coordinates (feet)
    is_third_shot: bool = False


@dataclass
class Rally:
    """A sequence of shots forming a single point."""
    shots: list[Shot]
    point_winner_team: int | None = None
    ending_type: str | None = None  # "winner", "error", "out"
    rally_number: int = 0

    @property
    def length(self) -> int:
        return len(self.shots)


class ShotClassifier:
    """Classifies shots based on ball trajectory, speed, and court position.

    Heuristic-based classification using:
    - Ball height trajectory (approximated from apparent size + vertical velocity)
    - Ball speed
    - Player and ball position relative to court zones
    - Shot sequence context (serves are first, returns are second, etc.)
    """

    # Speed thresholds (pixels/frame — calibrate based on video resolution)
    DINK_MAX_SPEED = 5.0
    DRIVE_MIN_SPEED = 12.0
    LOB_MIN_VERTICAL = -8.0  # Negative = upward in image coords

    def __init__(self, court_mapping: CourtMapping | None = None):
        self.court_mapping = court_mapping
        self.shot_count_in_rally = 0
        self._current_rally_shots: list[Shot] = []
        logger.info("ShotClassifier initialized")

    def classify(
        self,
        ball_positions: list[tuple[float, float]],
        ball_velocities: list[tuple[float, float]],
        hitting_player_id: int,
        hitting_player_team: int | None,
        hitting_player_pos: tuple[float, float],
        frame_idx: int,
    ) -> Shot:
        """Classify a shot based on ball trajectory and context.

        Args:
            ball_positions: Recent ball positions (last N frames).
            ball_velocities: Recent ball velocities.
            hitting_player_id: Tracker ID of the player hitting.
            hitting_player_team: Team (0 or 1).
            hitting_player_pos: Player position in image coords.
            frame_idx: Current frame index.

        Returns:
            Classified Shot object.
        """
        if not ball_velocities:
            return self._make_shot(
                frame_idx, ShotType.UNKNOWN, hitting_player_id,
                hitting_player_team, 0, ball_positions[-1] if ball_positions else (0, 0),
            )

        # Compute speed
        vx, vy = ball_velocities[-1]
        speed = np.sqrt(vx**2 + vy**2)

        ball_pos = ball_positions[-1] if ball_positions else (0, 0)
        court_pos = None
        zone = None

        # Get player court position for advanced shot detection
        player_court_pos = None
        if self.court_mapping:
            try:
                court_pos = self.court_mapping.image_to_court(ball_pos)
                zone = self.court_mapping.get_zone(court_pos)
            except Exception:
                pass
            try:
                player_court_pos = self.court_mapping.image_to_court(hitting_player_pos)
            except Exception:
                pass

        self.shot_count_in_rally += 1

        # Classify based on context
        shot_type = self._classify_type(
            speed, vx, vy, zone, self.shot_count_in_rally, court_pos,
            player_court_pos, hitting_player_id,
        )

        shot = self._make_shot(
            frame_idx, shot_type, hitting_player_id,
            hitting_player_team, speed, ball_pos, court_pos,
        )

        if self.shot_count_in_rally == 3:
            shot.is_third_shot = True

        self._current_rally_shots.append(shot)
        return shot

    def _classify_type(
        self,
        speed: float,
        vx: float,
        vy: float,
        zone: str | None,
        shot_number: int,
        court_pos: tuple[float, float] | None,
        player_court_pos: tuple[float, float] | None = None,
        player_id: int | None = None,
    ) -> ShotType:
        """Determine shot type from physics and context."""

        # Shot 1 = serve
        if shot_number == 1:
            return ShotType.SERVE

        # Shot 2 = return
        if shot_number == 2:
            return ShotType.RETURN

        # --- Advanced shot types (check before basic ones) ---

        # Erne: player outside sideline + near net + volley-like speed
        if player_court_pos and court_pos:
            px, py = player_court_pos
            if (px < -1 or px > COURT_WIDTH + 1) and abs(py - NET_POSITION) < KITCHEN_DEPTH:
                return ShotType.ERNE

        # ATP: ball trajectory goes outside court bounds laterally
        if court_pos:
            bx, _ = court_pos
            if (bx < -2 or bx > COURT_WIDTH + 2) and speed > self.DINK_MAX_SPEED:
                return ShotType.ATP

        # Poach: player crosses court midline (X=10ft) to intercept
        if player_court_pos and zone and "kitchen" in zone:
            px, _ = player_court_pos
            court_midline = COURT_WIDTH / 2
            # Check if player is on the opposite side of where they started
            if player_id is not None:
                # Simple heuristic: odd player IDs typically on left, even on right
                # More robust detection would track each player's home side
                expected_side = "left" if (player_id % 2 == 1) else "right"
                if expected_side == "left" and px > court_midline + 2:
                    return ShotType.POACH
                elif expected_side == "right" and px < court_midline - 2:
                    return ShotType.POACH

        # Speedup: sudden fast shot after 2+ dinks in the rally
        if speed >= self.DRIVE_MIN_SPEED and self._recent_dinks_count() >= 2:
            return ShotType.SPEEDUP

        # --- Standard shot types ---

        # Check for lob: strong upward component (negative vy in image coords)
        if vy < self.LOB_MIN_VERTICAL and speed > 6.0:
            return ShotType.LOB

        # Check for overhead: ball coming down fast + player near kitchen
        if vy > 8.0 and speed > self.DRIVE_MIN_SPEED:
            if zone and "kitchen" in zone:
                return ShotType.OVERHEAD

        # Kitchen zone + slow = dink
        if zone and "kitchen" in zone and speed <= self.DINK_MAX_SPEED:
            return ShotType.DINK

        # High speed from baseline/transition aimed down sideline = passing shot
        if speed >= self.DRIVE_MIN_SPEED and court_pos:
            bx, _ = court_pos
            near_sideline = bx < 3 or bx > COURT_WIDTH - 3
            if near_sideline and zone and ("baseline" in zone or "transition" in zone):
                return ShotType.PASSING

        # High speed = drive
        if speed >= self.DRIVE_MIN_SPEED:
            return ShotType.DRIVE

        # Reset: medium speed from transition/baseline zone, landing in kitchen
        # Differentiated from drop: reset happens after shot 3 (defensive context)
        if zone and ("transition" in zone or "baseline" in zone) and speed < self.DRIVE_MIN_SPEED:
            if shot_number > 3 and speed > self.DINK_MAX_SPEED:
                return ShotType.RESET

        # Medium speed from transition zone toward kitchen = drop
        if zone and "transition" in zone and speed < self.DRIVE_MIN_SPEED:
            return ShotType.DROP

        # Shot 3 special case: medium speed from baseline = likely drop attempt
        if shot_number == 3 and speed < self.DRIVE_MIN_SPEED:
            return ShotType.DROP

        # Near net + medium speed = volley
        if zone and "kitchen" in zone:
            return ShotType.VOLLEY

        # Default
        if speed < self.DINK_MAX_SPEED:
            return ShotType.DINK
        return ShotType.DRIVE

    def _recent_dinks_count(self) -> int:
        """Count consecutive dinks at the end of the current rally."""
        count = 0
        for shot in reversed(self._current_rally_shots):
            if shot.shot_type == ShotType.DINK:
                count += 1
            else:
                break
        return count

    def new_rally(self):
        """Reset for a new rally/point."""
        self.shot_count_in_rally = 0
        self._current_rally_shots = []

    def end_rally(self, winner_team: int | None = None, ending: str | None = None) -> Rally:
        """End current rally and return it."""
        rally = Rally(
            shots=list(self._current_rally_shots),
            point_winner_team=winner_team,
            ending_type=ending,
        )
        self.new_rally()
        return rally

    def _make_shot(
        self,
        frame_idx: int,
        shot_type: ShotType,
        player_id: int,
        team: int | None,
        speed: float,
        ball_pos: tuple[float, float],
        court_pos: tuple[float, float] | None = None,
    ) -> Shot:
        return Shot(
            frame_idx=frame_idx,
            shot_type=shot_type,
            outcome=ShotOutcome.UNKNOWN,
            player_id=player_id,
            team=team,
            ball_speed=speed,
            ball_position=ball_pos,
            court_position=court_pos,
        )
