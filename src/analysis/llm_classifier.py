"""Shot classification using vision LLM (Gemini / GPT-4o).

Hybrid approach: CV handles detection + tracking, LLM handles
the hard stuff — understanding what shots are being played,
game context, and scoring events.
"""

import base64
import json
import os
import cv2
import numpy as np
from dataclasses import dataclass
from pathlib import Path
from loguru import logger

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


@dataclass
class LLMShotEvent:
    """A shot event identified by the LLM."""
    frame_range: tuple[int, int]  # Start and end frame
    shot_type: str  # dink, drive, drop, lob, volley, serve, return, overhead, erne, atp, reset, speedup, passing, poach
    player_position: str  # near_left, near_right, far_left, far_right
    outcome: str  # in, out, net, winner, error, returned
    confidence: str  # high, medium, low
    notes: str = ""


@dataclass
class LLMRallyAnalysis:
    """Full rally analysis from the LLM."""
    shots: list[LLMShotEvent]
    rally_length: int
    point_winner: str | None  # "near_team" or "far_team"
    ending_type: str | None  # "winner", "unforced_error", "forced_error", "out", "net"
    key_moment: str = ""  # LLM's description of the decisive moment


@dataclass
class LLMMatchContext:
    """High-level match context from analyzing a segment."""
    events: list[LLMRallyAnalysis]
    observations: list[str]  # General observations about play style


# System prompt for the vision LLM
ANALYSIS_PROMPT = """You are an expert pickleball analyst. You are watching a doubles pickleball match.

Analyze the provided video frames and identify:

1. **Shot Events**: For each shot, identify:
   - shot_type: one of [serve, return, dink, drive, drop, lob, volley, overhead, erne, atp, reset, speedup, passing, poach]
     - erne: player jumps/runs around the kitchen to volley at the net post (player outside sideline)
     - atp: ball travels around the net post, not over it
     - reset: soft defensive shot from mid-court/baseline to neutralize and get to kitchen
     - speedup: sudden hard shot during a dink rally to catch opponent off guard (must follow 2+ dinks)
     - passing: fast shot aimed to pass an opponent at the net, typically down the sideline
     - poach: player crosses to partner's side to intercept a shot at the kitchen line
   - player_position: which player hit it [near_left, near_right, far_left, far_right]
     (near = closer to camera, far = further from camera)
   - outcome: [in, out, net, winner, error, returned]
   - confidence: [high, medium, low]

2. **Rally Analysis**:
   - How many shots in the rally
   - Who won the point (near_team or far_team)
   - How did the point end (winner, unforced_error, forced_error, out, net)
   - What was the key moment

3. **Player Observations** (if visible):
   - Court positioning tendencies
   - Shot selection patterns
   - Strengths/weaknesses you can identify

Respond in this exact JSON format:
```json
{
  "rallies": [
    {
      "shots": [
        {
          "frame_range": [0, 30],
          "shot_type": "serve",
          "player_position": "near_right",
          "outcome": "in",
          "confidence": "high",
          "notes": ""
        }
      ],
      "rally_length": 5,
      "point_winner": "near_team",
      "ending_type": "unforced_error",
      "key_moment": "Far left player hit a drive into the net on the 5th shot"
    }
  ],
  "observations": [
    "Near team has strong dink game",
    "Far right player tends to speed up too early"
  ]
}
```

Be precise. If you can't clearly see a shot, mark confidence as "low".
Focus on what you can actually see in the frames."""


class LLMClassifier:
    """Uses a vision LLM to classify shots and analyze rallies.

    Sends batches of frames (annotated with player/ball bounding boxes
    from the CV pipeline) to the LLM for analysis.
    """

    def __init__(
        self,
        provider: str = "gemini",  # "gemini" or "openai"
        model: str | None = None,
        frames_per_batch: int = 16,  # Frames to send per LLM call
        batch_interval_seconds: float = 5.0,  # Analyze every N seconds of video
    ):
        self.provider = provider
        self.frames_per_batch = frames_per_batch
        self.batch_interval_seconds = batch_interval_seconds

        if provider == "gemini":
            if not HAS_GEMINI:
                raise ImportError("google-generativeai not installed. pip install google-generativeai")
            api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("Set GEMINI_API_KEY or GOOGLE_API_KEY env var")
            genai.configure(api_key=api_key)
            self.model_name = model or "gemini-2.5-pro"
            self.model = genai.GenerativeModel(self.model_name)
            logger.info(f"LLM Classifier: Gemini ({self.model_name})")

        elif provider == "openai":
            if not HAS_OPENAI:
                raise ImportError("openai not installed. pip install openai")
            self.client = openai.OpenAI()
            self.model_name = model or "gpt-4o"
            logger.info(f"LLM Classifier: OpenAI ({self.model_name})")

        else:
            raise ValueError(f"Unknown provider: {provider}. Use 'gemini' or 'openai'.")

    def analyze_frames(
        self,
        frames: list[np.ndarray],
        frame_indices: list[int],
        annotations: list[dict] | None = None,
    ) -> LLMMatchContext:
        """Send a batch of frames to the LLM for analysis.

        Args:
            frames: List of BGR frames (OpenCV format).
            frame_indices: Corresponding frame indices in the video.
            annotations: Optional per-frame annotation data (player boxes, ball pos).

        Returns:
            LLMMatchContext with identified events.
        """
        # Annotate frames with bounding boxes if provided
        annotated_frames = []
        for i, frame in enumerate(frames):
            annotated = frame.copy()
            if annotations and i < len(annotations):
                annotated = self._draw_annotations(annotated, annotations[i])
            annotated_frames.append(annotated)

        # Subsample if too many frames
        if len(annotated_frames) > self.frames_per_batch:
            step = len(annotated_frames) // self.frames_per_batch
            annotated_frames = annotated_frames[::step][:self.frames_per_batch]

        # Encode frames
        encoded = [self._encode_frame(f) for f in annotated_frames]

        # Call LLM
        if self.provider == "gemini":
            return self._analyze_gemini(encoded, frame_indices)
        else:
            return self._analyze_openai(encoded, frame_indices)

    def _analyze_gemini(
        self, encoded_frames: list[str], frame_indices: list[int]
    ) -> LLMMatchContext:
        """Analyze using Gemini."""
        parts = [ANALYSIS_PROMPT, f"\nFrame indices: {frame_indices}\n"]

        for i, b64 in enumerate(encoded_frames):
            parts.append({
                "mime_type": "image/jpeg",
                "data": base64.b64decode(b64),
            })

        try:
            response = self.model.generate_content(parts)
            return self._parse_response(response.text)
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            return LLMMatchContext(events=[], observations=[])

    def _analyze_openai(
        self, encoded_frames: list[str], frame_indices: list[int]
    ) -> LLMMatchContext:
        """Analyze using OpenAI GPT-4o."""
        content = [
            {"type": "text", "text": ANALYSIS_PROMPT + f"\nFrame indices: {frame_indices}\n"},
        ]

        for b64 in encoded_frames:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "high"},
            })

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": content}],
                max_tokens=4096,
                response_format={"type": "json_object"},
            )
            return self._parse_response(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            return LLMMatchContext(events=[], observations=[])

    def _parse_response(self, text: str) -> LLMMatchContext:
        """Parse LLM JSON response into structured data."""
        try:
            # Extract JSON from response (handle markdown code blocks)
            text = text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            if text.endswith("```"):
                text = text[:-3]

            data = json.loads(text.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}\nResponse: {text[:500]}")
            return LLMMatchContext(events=[], observations=[])

        events = []
        for rally_data in data.get("rallies", []):
            shots = []
            for shot_data in rally_data.get("shots", []):
                shots.append(LLMShotEvent(
                    frame_range=tuple(shot_data.get("frame_range", [0, 0])),
                    shot_type=shot_data.get("shot_type", "unknown"),
                    player_position=shot_data.get("player_position", "unknown"),
                    outcome=shot_data.get("outcome", "unknown"),
                    confidence=shot_data.get("confidence", "low"),
                    notes=shot_data.get("notes", ""),
                ))

            events.append(LLMRallyAnalysis(
                shots=shots,
                rally_length=rally_data.get("rally_length", len(shots)),
                point_winner=rally_data.get("point_winner"),
                ending_type=rally_data.get("ending_type"),
                key_moment=rally_data.get("key_moment", ""),
            ))

        observations = data.get("observations", [])
        return LLMMatchContext(events=events, observations=observations)

    @staticmethod
    def _encode_frame(frame: np.ndarray, quality: int = 80) -> str:
        """Encode frame as base64 JPEG."""
        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
        return base64.b64encode(buffer).decode("utf-8")

    @staticmethod
    def _draw_annotations(frame: np.ndarray, annotations: dict) -> np.ndarray:
        """Draw player/ball annotations on frame for LLM context.

        Args:
            annotations: {
                "players": [{"bbox": [x1,y1,x2,y2], "id": int, "team": int}],
                "ball": {"center": (x, y), "radius": float} | None
            }
        """
        annotated = frame.copy()

        # Draw player boxes
        team_colors = {0: (0, 255, 0), 1: (255, 0, 0)}  # Green=near, Blue=far
        for player in annotations.get("players", []):
            bbox = player["bbox"]
            color = team_colors.get(player.get("team"), (255, 255, 255))
            x1, y1, x2, y2 = [int(v) for v in bbox]
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            label = f"P{player.get('id', '?')}"
            cv2.putText(annotated, label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # Draw ball
        ball = annotations.get("ball")
        if ball:
            cx, cy = [int(v) for v in ball["center"]]
            r = max(int(ball.get("radius", 8)), 5)
            cv2.circle(annotated, (cx, cy), r, (0, 255, 255), 2)  # Yellow
            cv2.putText(annotated, "BALL", (cx + r + 2, cy),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        return annotated
