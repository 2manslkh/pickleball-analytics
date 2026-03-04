"""Main video analysis pipeline — supports CV-only (Option B) and Hybrid CV+LLM (Option C).

CV handles: player detection, ball detection, tracking, court mapping.
LLM handles (hybrid only): shot classification, rally analysis, game events.
"""

import cv2
import json
import numpy as np
from enum import Enum
from pathlib import Path
from loguru import logger
from tqdm import tqdm

from src.detection.player_detector import PlayerDetector
from src.detection.ball_detector import BallDetector
from src.tracking.tracker import MultiObjectTracker
from src.court.court_detector import CourtDetector
from src.analysis.shot_classifier import ShotClassifier, Shot, ShotType, ShotOutcome, Rally
from src.analysis.stats import StatsAggregator, MatchStats


class AnalysisMode(str, Enum):
    CV_ONLY = "cv"      # Option B: Pure CV with heuristic shot classification
    HYBRID = "hybrid"   # Option C: CV + LLM for shot classification


class AnalysisPipeline:
    """End-to-end video analysis pipeline.

    Supports two modes:
    - CV_ONLY: YOLO detection + ByteTrack + heuristic shot classifier. Free, fast, offline.
    - HYBRID: Same CV base + vision LLM for shot classification. More accurate, costs money.
    """

    def __init__(
        self,
        mode: AnalysisMode = AnalysisMode.HYBRID,
        player_model: str = "yolov8n.pt",
        player_confidence: float = 0.5,
        ball_confidence: float = 0.3,
        sample_rate: int = 2,
        # LLM options (hybrid mode only)
        llm_provider: str = "gemini",
        llm_model: str | None = None,
        llm_batch_seconds: float = 10.0,
        llm_frames_per_batch: int = 16,
    ):
        self.mode = mode
        self.player_detector = PlayerDetector(player_model, player_confidence)
        self.ball_detector = BallDetector(player_model, ball_confidence)
        self.tracker = MultiObjectTracker()
        self.court_detector = CourtDetector()
        self.sample_rate = sample_rate

        # Mode-specific setup
        if mode == AnalysisMode.HYBRID:
            from src.analysis.llm_classifier import LLMClassifier
            self.llm_classifier = LLMClassifier(
                provider=llm_provider,
                model=llm_model,
                frames_per_batch=llm_frames_per_batch,
                batch_interval_seconds=llm_batch_seconds,
            )
            self.llm_batch_seconds = llm_batch_seconds
        else:
            self.llm_classifier = None
            self.llm_batch_seconds = 0

        # CV-only mode state
        self.shot_classifier = ShotClassifier()
        self._last_ball_holder: int | None = None
        self._frames_since_hit = 0
        self._rally_active = False

        logger.info(f"Pipeline initialized in {mode.value} mode")

    def analyze(self, video_path: str | Path) -> MatchStats:
        """Run full analysis on a video."""
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
            f"Analyzing ({self.mode.value}): {video_path.name} | "
            f"{width}x{height} @ {fps:.1f}fps | "
            f"{total_frames} frames ({total_frames/fps:.1f}s)"
        )

        if self.mode == AnalysisMode.HYBRID:
            return self._analyze_hybrid(cap, fps, total_frames)
        else:
            return self._analyze_cv_only(cap, fps, total_frames)

    # ── CV-Only Mode (Option B) ────────────────────────────────

    def _analyze_cv_only(
        self, cap: cv2.VideoCapture, fps: float, total_frames: int
    ) -> MatchStats:
        """Pure CV analysis with heuristic shot classification."""
        stats = StatsAggregator()
        court_mapping = None
        frame_idx = 0

        pbar = tqdm(total=total_frames, desc="Analyzing (CV)", unit="frame")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % self.sample_rate == 0:
                # Court detection
                if court_mapping is None or frame_idx < int(fps * 3):
                    court_mapping = self.court_detector.detect(frame)
                    if court_mapping and not self.shot_classifier.court_mapping:
                        self.shot_classifier.court_mapping = court_mapping
                        logger.info(f"Court detected at frame {frame_idx}")

                # Player detection
                raw_detections = self.player_detector.detect(frame)
                players = self.player_detector.filter_players(raw_detections)

                # Ball detection
                ball = self.ball_detector.detect(frame)

                # Update tracker
                self.tracker.update_players(players, frame_idx)
                self.tracker.update_ball(ball.center if ball else None, frame_idx)

                # Zone tracking
                if court_mapping:
                    for player in self.tracker.get_active_players():
                        if player.last_position:
                            try:
                                court_pos = court_mapping.image_to_court(player.last_position)
                                zone = court_mapping.get_zone(court_pos)
                                stats.add_position_observation(player.tracker_id, zone)
                            except Exception:
                                pass

                # Shot detection (heuristic)
                self._detect_shots_cv(frame_idx, stats)

            frame_idx += 1
            pbar.update(1)

        pbar.close()
        cap.release()

        # Assign teams
        self._assign_teams(court_mapping)

        # End open rally
        if self._rally_active:
            rally = self.shot_classifier.end_rally()
            if rally.shots:
                stats.add_rally(rally)

        # Set player teams
        for pid, player in self.tracker.players.items():
            if player.team is not None:
                stats.player_teams[pid] = player.team

        match_stats = stats.compute(fps=fps, total_frames=frame_idx)
        logger.info(
            f"CV analysis complete: {match_stats.total_rallies} rallies, "
            f"{sum(p.total_shots for p in match_stats.players)} shots"
        )
        return match_stats

    def _detect_shots_cv(self, frame_idx: int, stats: StatsAggregator):
        """Detect shots using ball velocity changes (CV-only mode)."""
        ball = self.tracker.ball
        if len(ball.velocities) < 3:
            return

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
            # End rally after long pause
            if self._rally_active and self._frames_since_hit > 90:
                rally = self.shot_classifier.end_rally()
                if rally.shots:
                    stats.add_rally(rally)
                self._rally_active = False
            return

        if self._frames_since_hit < 5:
            return
        self._frames_since_hit = 0

        # Find closest player
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

        if closest_player is None or min_dist > 200:
            return

        if not self._rally_active:
            self._rally_active = True
            self.shot_classifier.new_rally()

        shot = self.shot_classifier.classify(
            ball_positions=ball.positions[-10:],
            ball_velocities=ball.velocities[-10:],
            hitting_player_id=closest_player.tracker_id,
            hitting_player_team=closest_player.team,
            hitting_player_pos=closest_player.last_position,
            frame_idx=frame_idx,
        )

        logger.debug(f"Shot: {shot.shot_type.value} by P{shot.player_id} @ frame {frame_idx}")

    # ── Hybrid Mode (Option C) ─────────────────────────────────

    def _analyze_hybrid(
        self, cap: cv2.VideoCapture, fps: float, total_frames: int
    ) -> MatchStats:
        """Hybrid CV + LLM analysis."""
        from src.analysis.llm_classifier import LLMMatchContext

        # Phase 1: CV pass
        logger.info("Phase 1: CV detection & tracking...")
        cv_data = self._run_cv_pass(cap, fps, total_frames)
        cap.release()

        # Phase 2: LLM pass
        logger.info("Phase 2: Vision LLM analysis...")
        llm_results = self._run_llm_pass(cv_data, fps)

        # Phase 3: Merge
        logger.info("Phase 3: Computing statistics...")
        stats = self._merge_and_compute(cv_data, llm_results, fps, total_frames)

        logger.info(
            f"Hybrid analysis complete: {stats.total_rallies} rallies, "
            f"{sum(p.total_shots for p in stats.players)} shots"
        )
        return stats

    def _run_cv_pass(self, cap: cv2.VideoCapture, fps: float, total_frames: int) -> dict:
        """Phase 1: CV detection and tracking."""
        frames_for_llm = []
        frame_indices_for_llm = []
        annotations_for_llm = []
        zone_observations = {}

        court_mapping = None
        batch_interval_frames = int(self.llm_batch_seconds * fps)
        llm_sample_interval = max(1, batch_interval_frames // self.llm_classifier.frames_per_batch)

        frame_idx = 0
        pbar = tqdm(total=total_frames, desc="Phase 1: CV", unit="frame")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % self.sample_rate == 0:
                if court_mapping is None or frame_idx < int(fps * 3):
                    court_mapping = self.court_detector.detect(frame)

                raw_detections = self.player_detector.detect(frame)
                players = self.player_detector.filter_players(raw_detections)
                ball = self.ball_detector.detect(frame)

                self.tracker.update_players(players, frame_idx)
                self.tracker.update_ball(ball.center if ball else None, frame_idx)

                if court_mapping:
                    for player in self.tracker.get_active_players():
                        if player.last_position:
                            try:
                                court_pos = court_mapping.image_to_court(player.last_position)
                                zone = court_mapping.get_zone(court_pos)
                                if player.tracker_id not in zone_observations:
                                    zone_observations[player.tracker_id] = []
                                zone_observations[player.tracker_id].append(zone)
                            except Exception:
                                pass

                if frame_idx % llm_sample_interval == 0:
                    annotation = {
                        "players": [
                            {
                                "bbox": p.detections[-1].bbox.tolist() if p.detections else [],
                                "id": p.tracker_id,
                                "team": p.team,
                            }
                            for p in self.tracker.get_active_players()
                            if p.detections
                        ],
                        "ball": {
                            "center": ball.center,
                            "radius": ball.radius,
                        } if ball else None,
                    }
                    frames_for_llm.append(frame.copy())
                    frame_indices_for_llm.append(frame_idx)
                    annotations_for_llm.append(annotation)

            frame_idx += 1
            pbar.update(1)

        pbar.close()

        self._assign_teams(court_mapping)

        return {
            "frames": frames_for_llm,
            "frame_indices": frame_indices_for_llm,
            "annotations": annotations_for_llm,
            "court_mapping": court_mapping,
            "zone_observations": zone_observations,
            "tracker": self.tracker,
        }

    def _run_llm_pass(self, cv_data: dict, fps: float) -> list:
        """Phase 2: Send frame batches to vision LLM."""
        frames = cv_data["frames"]
        indices = cv_data["frame_indices"]
        annotations = cv_data["annotations"]

        if not frames:
            logger.warning("No frames collected for LLM analysis")
            return []

        batch_size = self.llm_classifier.frames_per_batch
        results = []
        total_batches = (len(frames) + batch_size - 1) // batch_size
        pbar = tqdm(total=total_batches, desc="Phase 2: LLM", unit="batch")

        for i in range(0, len(frames), batch_size):
            batch_frames = frames[i:i + batch_size]
            batch_indices = indices[i:i + batch_size]
            batch_annotations = annotations[i:i + batch_size]

            result = self.llm_classifier.analyze_frames(
                batch_frames, batch_indices, batch_annotations,
            )
            results.append(result)
            pbar.update(1)

        pbar.close()
        return results

    def _merge_and_compute(
        self, cv_data: dict, llm_results: list, fps: float, total_frames: int,
    ) -> MatchStats:
        """Phase 3: Merge CV tracking + LLM analysis."""
        stats = StatsAggregator()
        tracker = cv_data["tracker"]
        position_to_player = self._map_positions_to_players(tracker)

        for context in llm_results:
            for rally_analysis in context.events:
                shots = []
                for llm_shot in rally_analysis.shots:
                    try:
                        shot_type = ShotType(llm_shot.shot_type)
                    except ValueError:
                        shot_type = ShotType.UNKNOWN
                    try:
                        outcome = ShotOutcome(llm_shot.outcome)
                    except ValueError:
                        outcome = ShotOutcome.UNKNOWN

                    player_id = position_to_player.get(llm_shot.player_position, -1)
                    team = None
                    if player_id >= 0 and player_id in tracker.players:
                        team = tracker.players[player_id].team

                    shot = Shot(
                        frame_idx=llm_shot.frame_range[0],
                        shot_type=shot_type,
                        outcome=outcome,
                        player_id=player_id,
                        team=team,
                        ball_speed=0,
                        ball_position=(0, 0),
                        court_position=None,
                        is_third_shot=(len(shots) == 2 and shot_type == ShotType.DROP),
                    )
                    shots.append(shot)

                winner_team = None
                if rally_analysis.point_winner == "near_team":
                    winner_team = 0
                elif rally_analysis.point_winner == "far_team":
                    winner_team = 1

                rally = Rally(
                    shots=shots,
                    point_winner_team=winner_team,
                    ending_type=rally_analysis.ending_type,
                )
                stats.add_rally(rally)

        for pid, zones in cv_data["zone_observations"].items():
            for zone in zones:
                stats.add_position_observation(pid, zone)

        for pid, player in tracker.players.items():
            if player.team is not None:
                stats.player_teams[pid] = player.team

        match_stats = stats.compute(fps=fps, total_frames=total_frames)

        all_observations = []
        for context in llm_results:
            all_observations.extend(context.observations)
        if all_observations:
            match_stats.llm_observations = all_observations

        return match_stats

    # ── Shared Helpers ──────────────────────────────────────────

    def _assign_teams(self, court_mapping):
        """Assign players to teams based on court position."""
        if court_mapping:
            try:
                midline_img = court_mapping.court_to_image((10, 22))
                self.tracker.assign_teams(midline_img[1])
            except Exception:
                self.tracker.assign_teams()
        else:
            self.tracker.assign_teams()

    def _map_positions_to_players(self, tracker: MultiObjectTracker) -> dict[str, int]:
        """Map LLM position names to tracker player IDs."""
        active = tracker.get_active_players(max_gap=9999)
        if not active:
            return {}

        mapping = {}
        near = [p for p in active if p.team == 0]
        far = [p for p in active if p.team == 1]

        def avg_x(player):
            if player.positions:
                return np.mean([pos[0] for pos in player.positions[-100:]])
            return 0

        near.sort(key=avg_x)
        far.sort(key=avg_x)

        if len(near) >= 1:
            mapping["near_left"] = near[0].tracker_id
        if len(near) >= 2:
            mapping["near_right"] = near[1].tracker_id
        if len(far) >= 1:
            mapping["far_left"] = far[0].tracker_id
        if len(far) >= 2:
            mapping["far_right"] = far[1].tracker_id

        logger.info(f"Position mapping: {mapping}")
        return mapping
