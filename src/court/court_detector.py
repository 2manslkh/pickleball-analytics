"""Court detection and homography mapping."""

import cv2
import numpy as np
from dataclasses import dataclass
from loguru import logger


# Standard pickleball court dimensions (feet)
COURT_WIDTH = 20.0
COURT_LENGTH = 44.0
KITCHEN_DEPTH = 7.0  # Non-volley zone from net
NET_POSITION = COURT_LENGTH / 2  # 22 feet from each baseline


@dataclass
class CourtKeypoints:
    """Court corner/line intersection points in image coordinates."""
    # Corners: [top-left, top-right, bottom-right, bottom-left]
    corners: np.ndarray  # Shape: (4, 2)
    # Kitchen lines (optional, for more accurate mapping)
    kitchen_near: np.ndarray | None = None  # Near side kitchen line endpoints
    kitchen_far: np.ndarray | None = None   # Far side kitchen line endpoints


@dataclass
class CourtMapping:
    """Homography mapping between image and real-world court coordinates."""
    homography: np.ndarray  # 3x3 homography matrix
    inv_homography: np.ndarray  # Inverse for court→image mapping
    keypoints: CourtKeypoints

    def image_to_court(self, point: tuple[float, float]) -> tuple[float, float]:
        """Map image pixel coordinates to court coordinates (feet)."""
        pt = np.array([[[point[0], point[1]]]], dtype=np.float64)
        result = cv2.perspectiveTransform(pt, self.homography)
        return (float(result[0][0][0]), float(result[0][0][1]))

    def court_to_image(self, point: tuple[float, float]) -> tuple[float, float]:
        """Map court coordinates (feet) to image pixel coordinates."""
        pt = np.array([[[point[0], point[1]]]], dtype=np.float64)
        result = cv2.perspectiveTransform(pt, self.inv_homography)
        return (float(result[0][0][0]), float(result[0][0][1]))

    def is_in_kitchen(self, court_point: tuple[float, float]) -> bool:
        """Check if a court-space point is in the kitchen (non-volley zone)."""
        x, y = court_point
        if x < 0 or x > COURT_WIDTH:
            return False
        # Near kitchen: y between net and kitchen line
        near_kitchen = (NET_POSITION - KITCHEN_DEPTH) <= y <= NET_POSITION
        # Far kitchen: y between net and far kitchen line
        far_kitchen = NET_POSITION <= y <= (NET_POSITION + KITCHEN_DEPTH)
        return near_kitchen or far_kitchen

    def get_zone(self, court_point: tuple[float, float]) -> str:
        """Classify a court position into a zone.

        Returns one of:
            'near_baseline', 'near_transition', 'near_kitchen',
            'far_kitchen', 'far_transition', 'far_baseline',
            'out_of_bounds'
        """
        x, y = court_point
        if x < -1 or x > COURT_WIDTH + 1 or y < -1 or y > COURT_LENGTH + 1:
            return "out_of_bounds"

        if y < NET_POSITION - KITCHEN_DEPTH:
            if y < NET_POSITION - KITCHEN_DEPTH - 8:
                return "near_baseline"
            return "near_transition"
        elif y < NET_POSITION:
            return "near_kitchen"
        elif y < NET_POSITION + KITCHEN_DEPTH:
            return "far_kitchen"
        elif y < NET_POSITION + KITCHEN_DEPTH + 8:
            return "far_transition"
        else:
            return "far_baseline"


class CourtDetector:
    """Detects the pickleball court in video frames.

    Uses a combination of:
    1. Line detection (Hough transform)
    2. Color segmentation (court surface color)
    3. Geometric constraints (known court aspect ratio)
    """

    def __init__(self):
        # Real-world court corners (feet) — standard orientation
        # Origin at near-side left corner, Y increases toward far baseline
        self.court_corners_real = np.array([
            [0, 0],                       # Near-left
            [COURT_WIDTH, 0],             # Near-right
            [COURT_WIDTH, COURT_LENGTH],  # Far-right
            [0, COURT_LENGTH],            # Far-left
        ], dtype=np.float64)

        self._cached_mapping: CourtMapping | None = None
        logger.info("CourtDetector initialized")

    def detect(self, frame: np.ndarray) -> CourtMapping | None:
        """Detect court in a frame and compute homography.

        Args:
            frame: BGR image.

        Returns:
            CourtMapping if court found, None otherwise.
        """
        lines = self._detect_lines(frame)
        if lines is None or len(lines) < 4:
            return self._cached_mapping  # Fall back to cached

        corners = self._find_court_corners(lines, frame.shape)
        if corners is None:
            return self._cached_mapping

        keypoints = CourtKeypoints(corners=corners)
        homography, mask = cv2.findHomography(
            corners.astype(np.float64),
            self.court_corners_real,
            cv2.RANSAC,
            5.0,
        )

        if homography is None:
            return self._cached_mapping

        inv_homography = np.linalg.inv(homography)

        mapping = CourtMapping(
            homography=homography,
            inv_homography=inv_homography,
            keypoints=keypoints,
        )
        self._cached_mapping = mapping
        return mapping

    def detect_from_keypoints(self, corners: np.ndarray) -> CourtMapping:
        """Create mapping from manually specified court corners.

        Args:
            corners: 4 corner points in image coordinates,
                     ordered [near-left, near-right, far-right, far-left].

        Returns:
            CourtMapping object.
        """
        homography, _ = cv2.findHomography(
            corners.astype(np.float64),
            self.court_corners_real,
            cv2.RANSAC,
            5.0,
        )
        inv_homography = np.linalg.inv(homography)

        mapping = CourtMapping(
            homography=homography,
            inv_homography=inv_homography,
            keypoints=CourtKeypoints(corners=corners),
        )
        self._cached_mapping = mapping
        return mapping

    def _detect_lines(self, frame: np.ndarray) -> np.ndarray | None:
        """Detect lines using Canny + Hough transform."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 50, 150)

        # Dilate to connect broken lines
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)

        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180,
            threshold=80,
            minLineLength=50,
            maxLineGap=20,
        )
        return lines

    def _find_court_corners(
        self, lines: np.ndarray, frame_shape: tuple
    ) -> np.ndarray | None:
        """Extract court corners from detected lines.

        Groups lines into horizontal/vertical, finds intersections,
        and selects the 4 corners that best match court geometry.
        """
        h, w = frame_shape[:2]
        horizontal = []
        vertical = []

        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)

            if angle < 30 or angle > 150:
                horizontal.append(line[0])
            elif 60 < angle < 120:
                vertical.append(line[0])

        if len(horizontal) < 2 or len(vertical) < 2:
            return None

        # Find intersections
        intersections = []
        for hl in horizontal:
            for vl in vertical:
                pt = self._line_intersection(hl, vl)
                if pt is not None and 0 <= pt[0] <= w and 0 <= pt[1] <= h:
                    intersections.append(pt)

        if len(intersections) < 4:
            return None

        # Cluster intersections and find 4 corners
        points = np.array(intersections)

        # Use convex hull to find outermost points
        if len(points) < 4:
            return None

        hull = cv2.convexHull(points.astype(np.float32))
        if len(hull) < 4:
            return None

        # Approximate hull to 4 points (quadrilateral)
        epsilon = 0.02 * cv2.arcLength(hull, True)
        approx = cv2.approxPolyDP(hull, epsilon, True)

        if len(approx) == 4:
            corners = approx.reshape(4, 2)
            # Order: top-left, top-right, bottom-right, bottom-left
            return self._order_corners(corners)

        # If approx didn't give 4 points, take the 4 extreme hull points
        hull_points = hull.reshape(-1, 2)
        if len(hull_points) >= 4:
            # Sort by angle from centroid
            centroid = hull_points.mean(axis=0)
            angles = np.arctan2(
                hull_points[:, 1] - centroid[1],
                hull_points[:, 0] - centroid[0],
            )
            sorted_idx = np.argsort(angles)
            step = len(sorted_idx) // 4
            corners = hull_points[[sorted_idx[i * step] for i in range(4)]]
            return self._order_corners(corners)

        return None

    @staticmethod
    def _line_intersection(
        line1: np.ndarray, line2: np.ndarray
    ) -> tuple[float, float] | None:
        """Find intersection of two lines defined by endpoints."""
        x1, y1, x2, y2 = line1
        x3, y3, x4, y4 = line2

        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(denom) < 1e-10:
            return None

        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        px = x1 + t * (x2 - x1)
        py = y1 + t * (y2 - y1)
        return (px, py)

    @staticmethod
    def _order_corners(corners: np.ndarray) -> np.ndarray:
        """Order corners as [top-left, top-right, bottom-right, bottom-left]."""
        # Sort by Y first
        sorted_by_y = corners[np.argsort(corners[:, 1])]
        # Top two sorted by X
        top = sorted_by_y[:2][np.argsort(sorted_by_y[:2, 0])]
        # Bottom two sorted by X
        bottom = sorted_by_y[2:][np.argsort(sorted_by_y[2:, 0])]

        return np.array([top[0], top[1], bottom[1], bottom[0]])
