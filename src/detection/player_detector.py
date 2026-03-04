"""Player detection using YOLOv8."""

from ultralytics import YOLO
import numpy as np
from dataclasses import dataclass
from loguru import logger


@dataclass
class Detection:
    """A single player detection."""
    bbox: np.ndarray  # [x1, y1, x2, y2]
    confidence: float
    class_id: int  # 0 = person

    @property
    def center(self) -> tuple[float, float]:
        return (
            (self.bbox[0] + self.bbox[2]) / 2,
            (self.bbox[1] + self.bbox[3]) / 2,
        )

    @property
    def bottom_center(self) -> tuple[float, float]:
        """Feet position — best for court mapping."""
        return (
            (self.bbox[0] + self.bbox[2]) / 2,
            self.bbox[3],
        )

    @property
    def width(self) -> float:
        return self.bbox[2] - self.bbox[0]

    @property
    def height(self) -> float:
        return self.bbox[3] - self.bbox[1]

    @property
    def area(self) -> float:
        return self.width * self.height


class PlayerDetector:
    """Detects players in video frames using YOLOv8."""

    PERSON_CLASS_ID = 0  # COCO class for person

    def __init__(self, model_path: str = "yolov8n.pt", confidence: float = 0.5):
        """
        Args:
            model_path: Path to YOLO model weights. Default uses pretrained nano model.
            confidence: Minimum confidence threshold.
        """
        self.model = YOLO(model_path)
        self.confidence = confidence
        logger.info(f"PlayerDetector initialized with {model_path}, conf={confidence}")

    def detect(self, frame: np.ndarray) -> list[Detection]:
        """Detect players in a single frame.

        Args:
            frame: BGR image (OpenCV format).

        Returns:
            List of Detection objects for people found.
        """
        results = self.model(frame, conf=self.confidence, verbose=False)[0]
        detections = []

        for box in results.boxes:
            class_id = int(box.cls[0])
            if class_id != self.PERSON_CLASS_ID:
                continue

            detections.append(Detection(
                bbox=box.xyxy[0].cpu().numpy(),
                confidence=float(box.conf[0]),
                class_id=class_id,
            ))

        return detections

    def filter_players(
        self,
        detections: list[Detection],
        min_area: float = 2000,
        max_count: int = 4,
    ) -> list[Detection]:
        """Filter detections to likely pickleball players.

        Removes small detections (spectators far away) and keeps
        at most max_count (4 for doubles).

        Args:
            detections: Raw detections from detect().
            min_area: Minimum bounding box area in pixels.
            max_count: Maximum number of players to keep.

        Returns:
            Filtered list of player detections, sorted by area (largest first).
        """
        # Filter by size
        filtered = [d for d in detections if d.area >= min_area]

        # Sort by area descending (players on court are bigger than spectators)
        filtered.sort(key=lambda d: d.area, reverse=True)

        # Keep top N
        return filtered[:max_count]
