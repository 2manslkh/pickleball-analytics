"""Main video analysis pipeline — Hybrid approach (Option C).

CV handles: player detection, ball detection, tracking, court mapping.
LLM handles: shot classification, rally analysis, game events.
"""

import cv2
import json
import numpy as np
from pathlib import Path
from loguru import logger
from tqdm import tqdm

from src.detection.player_detector import PlayerDetector
from src.detection.ball_detector import BallDetector
from src.tracking.tracker import MultiObjectTracker
from src.court.court_detector import CourtDetector
from src.analysis.llm_classifier import LLMClassifier, LLMMatchContext
from src.analysis.stats import StatsAggregator, MatchStats, PlayerStats


class AnalysisPipeline:
    """End-to-end video analysis pipeline (Hybrid: CV + LLM).

    Phase 1 (CV): Run through video, detect players + ball, track everything,
                  detect court, build per-frame annotations.
    Phase 2 (LLM): Send batched annotated frames to vision LLM for
                   shot classification and game event analysis.
    Phase 3 (Stats): Merge CV tracking data + LLM analysis into final stats.
    """

    def __init__(
        self,
        player_model: str = "yolov8n.pt",
        player_confidence: float = 0.5,
        ball_confidence: float = 0.3,
        sample_rate: int = 2,
        llm_provider: str = "gemini",
        llm_model: str | None = None,
        llm_batch_seconds: float = 10.0,
        llm_frames_per_batch: int = 16,
    ):
        self.player_detector = PlayerDetector(player_model, player_confidence)
        self.ball_detector = BallDetector(player_model, ball_confidence)
        self.tracker = MultiObjectTracker()
        self.court_detector = CourtDetector()
        self.llm_classifier = LLMClassifier(
            provider=llm_provider,
            model=llm_model,
            frames_per_batch=llm_frames_per_batch,
            batch_interval_seconds=llm_batch_seconds,
        )
        self.sample_rate = sample_rate
        self.llm_batch_seconds = llm_batch_seconds

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

        # ── Phase 1: CV Pass ──────────────────────────────────────
        logger.info("Phase 1: Running CV detection & tracking...")
        cv_data = self._run_cv_pass(cap, fps, total_frames)
        cap.release()

        # ── Phase 2: LLM Analysis ────────────────────────────────
        logger.info("Phase 2: Sending batches to vision LLM...")
        llm_results = self._run_llm_pass(cv_data, fps)

        # ── Phase 3: Merge & Compute Stats ────────────────────────
        logger.info("Phase 3: Computing final statistics...")
        stats = self._merge_and_compute(cv_data, llm_results, fps, total_frames)

        logger.info(
            f"Analysis complete: {stats.total_rallies} rallies, "
            f"{sum(p.total_shots for p in stats.players)} total shots"
        )

        return stats

    def _run_cv_pass(self, cap: cv2.VideoCapture, fps: float, total_frames: int) -> dict:
        """Phase 1: Run through video with CV models.

        Returns dict with:
            - frames: sampled frames for LLM
            - frame_indices: which frames were sampled
            - annotations: per-frame player/ball data
            - court_mapping: detected court mapping
            - zone_observations: {player_id: [zones]}
        """
        frames_for_llm = []
        frame_indices_for_llm = []
        annotations_for_llm = []
        zone_observations = {}

        court_mapping = None
        batch_interval_frames = int(self.llm_batch_seconds * fps)
        # Sample frames for LLM at regular intervals
        llm_sample_interval = max(1, batch_interval_frames // self.llm_classifier.frames_per_batch)

        frame_idx = 0
        pbar = tqdm(total=total_frames, desc="Phase 1: CV", unit="frame")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % self.sample_rate == 0:
                # Court detection (first 3 seconds, then cache)
                if court_mapping is None or frame_idx < int(fps * 3):
                    court_mapping = self.court_detector.detect(frame)

                # Player detection
                raw_detections = self.player_detector.detect(frame)
                players = self.player_detector.filter_players(raw_detections)

                # Ball detection
                ball = self.ball_detector.detect(frame)

                # Update tracker
                self.tracker.update_players(players, frame_idx)
                self.tracker.update_ball(
                    ball.center if ball else None,
                    frame_idx,
                )

                # Zone tracking
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

                # Sample frames for LLM
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

        # Assign teams
        if court_mapping:
            try:
                midline_img = court_mapping.court_to_image((10, 22))
                self.tracker.assign_teams(midline_img[1])
            except Exception:
                self.tracker.assign_teams()
        else:
            self.tracker.assign_teams()

        return {
            "frames": frames_for_llm,
            "frame_indices": frame_indices_for_llm,
            "annotations": annotations_for_llm,
            "court_mapping": court_mapping,
            "zone_observations": zone_observations,
            "tracker": self.tracker,
        }

    def _run_llm_pass(self, cv_data: dict, fps: float) -> list[LLMMatchContext]:
        """Phase 2: Send frame batches to vision LLM for analysis."""
        frames = cv_data["frames"]
        indices = cv_data["frame_indices"]
        annotations = cv_data["annotations"]

        if not frames:
            logger.warning("No frames collected for LLM analysis")
            return []

        # Batch frames
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
        self,
        cv_data: dict,
        llm_results: list[LLMMatchContext],
        fps: float,
        total_frames: int,
    ) -> MatchStats:
        """Phase 3: Merge CV tracking + LLM analysis into final stats."""
        stats = StatsAggregator()
        tracker = cv_data["tracker"]

        # Map LLM player positions to tracker IDs
        position_to_player = self._map_positions_to_players(tracker)

        # Process LLM rally data
        from src.analysis.shot_classifier import Shot, ShotType, ShotOutcome, Rally

        for context in llm_results:
            for rally_analysis in context.events:
                shots = []
                for llm_shot in rally_analysis.shots:
                    # Map LLM shot type to enum
                    try:
                        shot_type = ShotType(llm_shot.shot_type)
                    except ValueError:
                        shot_type = ShotType.UNKNOWN

                    try:
                        outcome = ShotOutcome(llm_shot.outcome)
                    except ValueError:
                        outcome = ShotOutcome.UNKNOWN

                    # Find player ID from position
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

                # Map point winner
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

        # Add zone observations from CV
        for pid, zones in cv_data["zone_observations"].items():
            for zone in zones:
                stats.add_position_observation(pid, zone)

        # Set player teams from tracker
        for pid, player in tracker.players.items():
            if player.team is not None:
                stats.player_teams[pid] = player.team

        # Compute final stats
        match_stats = stats.compute(fps=fps, total_frames=total_frames)

        # Add LLM observations as metadata
        all_observations = []
        for context in llm_results:
            all_observations.extend(context.observations)
        if all_observations:
            match_stats.llm_observations = all_observations

        return match_stats

    def _map_positions_to_players(self, tracker: MultiObjectTracker) -> dict[str, int]:
        """Map LLM position names to tracker player IDs.

        Uses average position of each player to assign:
        near_left, near_right, far_left, far_right
        """
        active = tracker.get_active_players(max_gap=9999)
        if not active:
            return {}

        mapping = {}

        # Split by team
        near = [p for p in active if p.team == 0]
        far = [p for p in active if p.team == 1]

        # Sort each team by average X position (left vs right)
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
