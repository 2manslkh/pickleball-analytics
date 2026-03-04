"""Main video analysis pipeline."""

import cv2
import numpy as np
from pathlib import Path
from loguru import logger
from tqdm import tqdm

from src.detection.player_detector import PlayerDetector
from src.detection.ball_detector import BallDetector
from src.tracking.tracker import MultiObjectTracker
from src.court.court_detector import CourtDetector
from src.analysis.shot_classifier import ShotClassifier, ShotType
from src.analysis.stats import StatsAggregator, MatchStats


class AnalysisPipeline:
    """End-to-end video analysis pipeline.

    Flow:
        1. Open video
        2. Detect court (first N frames, then cache)
        3. Per frame: detect players + ball, track, classify shots
        4. Aggregate stats
        5. Output report
    """

    def __init__(
        self,
        player_model: str = "yolov8n.pt",
        player_confidence: float = 0.5,
        ball_confidence: float = 0.3,
        sample_rate: int = 1,  # Process every Nth frame
    ):
        self.player_detector = PlayerDetector(player_model, player_confidence)
        self.ball_detector = BallDetector(player_model, ball_confidence)
        self.tracker = MultiObjectTracker()
        self.court_detector = CourtDetector()
        self.shot_classifier = ShotClassifier()
        self.stats = StatsAggregator()
        self.sample_rate = sample_rate

        # State for shot detection
        self._last_ball_holder: int | None = None
        self._ball_direction_changed = False
        self._frames_since_hit = 0
        self._rally_active = False

    def analyze(self, video_path: str | Path) -> MatchStats:
        """Run full analysis on a video.

        Args:
            video_path: Path to the match video file.

        Returns:
            MatchStats with all computed statistics.
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        logger.info(
            f"Analyzing: {video_path.name} | "
            f"{width}x{height} @ {fps:.1f}fps | "
            f"{total_frames} frames ({total_frames/fps:.1f}s)"
        )

        court_mapping = None
        frame_idx = 0

        pbar = tqdm(total=total_frames, desc="Analyzing", unit="frame")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % self.sample_rate == 0:
                # 1. Court detection (cache after first success)
                if court_mapping is None or frame_idx < 90:  # Re-detect first 3 sec
                    court_mapping = self.court_detector.detect(frame)
                    if court_mapping and frame_idx < 10:
                        self.shot_classifier.court_mapping = court_mapping
                        logger.info(f"Court detected at frame {frame_idx}")

                # 2. Player detection + filtering
                raw_detections = self.player_detector.detect(frame)
                players = self.player_detector.filter_players(raw_detections)

                # 3. Ball detection
                ball = self.ball_detector.detect(frame)

                # 4. Update tracker
                self.tracker.update_players(players, frame_idx)
                self.tracker.update_ball(
                    ball.center if ball else None,
                    frame_idx,
                )

                # 5. Position tracking for zone stats
                if court_mapping:
                    for player in self.tracker.get_active_players():
                        if player.last_position:
                            try:
                                court_pos = court_mapping.image_to_court(player.last_position)
                                zone = court_mapping.get_zone(court_pos)
                                self.stats.add_position_observation(player.tracker_id, zone)
                            except Exception:
                                pass

                # 6. Shot detection (detect contact events)
                self._detect_shots(frame_idx)

            frame_idx += 1
            pbar.update(1)

        pbar.close()
        cap.release()

        # Assign teams based on court position
        if court_mapping:
            midline_img = court_mapping.court_to_image((10, 22))
            self.tracker.assign_teams(midline_img[1])
        else:
            self.tracker.assign_teams()

        # End any open rally
        if self._rally_active:
            rally = self.shot_classifier.end_rally()
            if rally.shots:
                self.stats.add_rally(rally)

        # Update player teams in stats
        for pid, player in self.tracker.players.items():
            if player.team is not None:
                self.stats.player_teams[pid] = player.team

        # Compute final stats
        match_stats = self.stats.compute(fps=fps, total_frames=frame_idx)

        logger.info(
            f"Analysis complete: {match_stats.total_rallies} rallies, "
            f"{sum(p.total_shots for p in match_stats.players)} total shots"
        )

        return match_stats

    def _detect_shots(self, frame_idx: int):
        """Detect ball contact events (shot moments).

        Uses ball velocity changes to detect when a player hits the ball.
        A sudden change in ball direction = a shot was made.
        """
        ball = self.tracker.ball
        if len(ball.velocities) < 3:
            return

        # Check for direction reversal in ball trajectory
        recent_v = ball.velocities[-3:]
        vx_sign_change = (
            np.sign(recent_v[-1][0]) != np.sign(recent_v[-2][0])
            and abs(recent_v[-1][0]) > 1.0
        )
        vy_sign_change = (
            np.sign(recent_v[-1][1]) != np.sign(recent_v[-2][1])
            and abs(recent_v[-1][1]) > 1.0
        )
        speed_spike = (
            np.sqrt(recent_v[-1][0]**2 + recent_v[-1][1]**2) >
            np.sqrt(recent_v[-2][0]**2 + recent_v[-2][1]**2) * 1.5
        )

        if not (vx_sign_change or vy_sign_change or speed_spike):
            self._frames_since_hit += 1
            return

        # Minimum frames between hits (avoid double-counting)
        if self._frames_since_hit < 5:
            return
        self._frames_since_hit = 0

        # Find closest player to ball
        ball_pos = ball.positions[-1] if ball.positions else None
        if ball_pos is None:
            return

        closest_player = None
        min_dist = float("inf")

        for player in self.tracker.get_active_players():
            if player.last_position:
                dist = np.sqrt(
                    (player.last_position[0] - ball_pos[0])**2 +
                    (player.last_position[1] - ball_pos[1])**2
                )
                if dist < min_dist:
                    min_dist = dist
                    closest_player = player

        if closest_player is None or min_dist > 200:  # Too far = probably not a hit
            return

        # Start rally if needed
        if not self._rally_active:
            self._rally_active = True
            self.shot_classifier.new_rally()

        # Classify the shot
        shot = self.shot_classifier.classify(
            ball_positions=ball.positions[-10:],
            ball_velocities=ball.velocities[-10:],
            hitting_player_id=closest_player.tracker_id,
            hitting_player_team=closest_player.team,
            hitting_player_pos=closest_player.last_position,
            frame_idx=frame_idx,
        )

        logger.debug(
            f"Shot detected: {shot.shot_type.value} by player {shot.player_id} "
            f"at frame {frame_idx}"
        )

        # Detect rally end (long pause = point over)
        if self._frames_since_hit > 90:  # ~3 seconds at 30fps
            rally = self.shot_classifier.end_rally()
            if rally.shots:
                self.stats.add_rally(rally)
            self._rally_active = False
