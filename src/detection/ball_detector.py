"""Ball detection using YOLOv8 with pickleball-specific filtering."""

from ultralytics import YOLO
import numpy as np
import cv2
from dataclasses import dataclass
from loguru import logger


@dataclass
class BallDetection:
    """A single ball detection."""
    center: tuple[float, float]  # (x, y)
    radius: float
    confidence: float
    bbox: np.ndarray  # [x1, y1, x2, y2]


class BallDetector:
    """Detects the pickleball in video frames.

    Uses a combination of:
    1. YOLO sports ball detection (class 32 in COCO)
    2. Color-based filtering (pickleballs are typically bright yellow/green)
    3. Size filtering (ball should be small relative to frame)
    """

    SPORTS_BALL_CLASS_ID = 32  # COCO class

    # Pickleball color range in HSV (bright yellow-green)
    BALL_HSV_LOW = np.array([20, 100, 100])
    BALL_HSV_HIGH = np.array([45, 255, 255])

    def __init__(self, model_path: str = "yolov8n.pt", confidence: float = 0.3):
        self.model = YOLO(model_path)
        self.confidence = confidence
        self._last_positions: list[tuple[float, float]] = []
        logger.info(f"BallDetector initialized with {model_path}")

    def detect(self, frame: np.ndarray) -> BallDetection | None:
        """Detect the ball in a single frame.

        Tries YOLO first, falls back to color-based detection.

        Returns:
            BallDetection if found, None otherwise.
        """
        # Try YOLO detection first
        ball = self._detect_yolo(frame)
        if ball is not None:
            self._update_history(ball.center)
            return ball

        # Fallback: color-based detection
        ball = self._detect_color(frame)
        if ball is not None:
            self._update_history(ball.center)
            return ball

        return None

    def _detect_yolo(self, frame: np.ndarray) -> BallDetection | None:
        """Detect ball using YOLO."""
        results = self.model(frame, conf=self.confidence, verbose=False)[0]

        best = None
        best_conf = 0.0

        for box in results.boxes:
            class_id = int(box.cls[0])
            if class_id != self.SPORTS_BALL_CLASS_ID:
                continue

            conf = float(box.conf[0])
            if conf > best_conf:
                bbox = box.xyxy[0].cpu().numpy()
                cx = (bbox[0] + bbox[2]) / 2
                cy = (bbox[1] + bbox[3]) / 2
                radius = max(bbox[2] - bbox[0], bbox[3] - bbox[1]) / 2

                best = BallDetection(
                    center=(cx, cy),
                    radius=radius,
                    confidence=conf,
                    bbox=bbox,
                )
                best_conf = conf

        return best

    def _detect_color(self, frame: np.ndarray) -> BallDetection | None:
        """Detect ball using color filtering + contour detection."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.BALL_HSV_LOW, self.BALL_HSV_HIGH)

        # Morphological ops to clean up
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        best_candidate = None
        best_score = 0.0

        for contour in contours:
            area = cv2.contourArea(contour)

            # Ball should be small (roughly 10-50px diameter in typical footage)
            if area < 30 or area > 3000:
                continue

            # Check circularity
            perimeter = cv2.arcLength(contour, True)
            if perimeter == 0:
                continue
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            if circularity < 0.5:
                continue

            # Score by circularity and proximity to last known position
            (cx, cy), radius = cv2.minEnclosingCircle(contour)
            score = circularity

            if self._last_positions:
                last = self._last_positions[-1]
                dist = np.sqrt((cx - last[0])**2 + (cy - last[1])**2)
                # Closer to last position = higher score (ball doesn't teleport)
                score += max(0, 1.0 - dist / 200)

            if score > best_score:
                x1, y1 = cx - radius, cy - radius
                x2, y2 = cx + radius, cy + radius
                best_candidate = BallDetection(
                    center=(cx, cy),
                    radius=radius,
                    confidence=circularity * 0.5,  # Lower confidence for color-based
                    bbox=np.array([x1, y1, x2, y2]),
                )
                best_score = score

        return best_candidate

    def _update_history(self, pos: tuple[float, float], max_history: int = 10):
        """Keep a rolling buffer of recent ball positions."""
        self._last_positions.append(pos)
        if len(self._last_positions) > max_history:
            self._last_positions.pop(0)
