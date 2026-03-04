# Rally Detection & Segmentation

## Context
Rally detection is how we split a continuous video into discrete points. Currently we use ball velocity changes, which is fragile. PB Vision auto-segments rallies and removes dead time. We need robust rally boundaries.

## Current Approach (Fragile)
In `pipeline.py` (`_detect_shots_cv`):
- Detect ball direction change or speed spike → shot event
- If no shot for 90 frames (~3 sec) → end rally
- Problem: misses rallies when ball detection fails, creates false rallies from ball bouncing after point

## Better Approach: Multi-Signal Rally Detection

### Signals to Combine

1. **Ball activity** (current)
   - Ball detected and moving → rally active
   - Ball not detected for N frames → possible rally end

2. **Player positions** (new)
   - Rally start: players move to serve positions (one behind baseline, others at specific spots)
   - Rally active: players moving actively
   - Rally end: players stop, walk back, regroup
   - Dead time: players standing still, walking to bench, talking

3. **Player spacing** (new)
   - During play: players spread across court
   - Between rallies: players cluster, approach net for paddle tap, walk to sides

4. **Motion energy** (new)
   - Compute frame-to-frame pixel difference in player regions
   - High motion = rally active
   - Low motion = dead time
   - Spike after low period = rally start

5. **Serve detection** (strongest signal)
   - A serve always starts a rally
   - Detect serve: one player behind baseline, ball goes from their side to other side
   - This is the most reliable rally start signal

### Implementation

**File:** New `src/analysis/rally_detector.py`

```python
class RallyDetector:
    """Detects rally boundaries using multiple signals."""
    
    def __init__(self, fps: float = 30):
        self.fps = fps
        self.min_rally_duration = int(fps * 2)    # Min 2 sec
        self.max_dead_time = int(fps * 15)         # Max 15 sec between rallies
        self.min_dead_time = int(fps * 3)          # Min 3 sec dead time
    
    def detect_rallies(
        self,
        ball_positions: list[tuple | None],     # None = not detected
        player_positions: dict[int, list[tuple]],  # per player per frame
        frame_count: int,
    ) -> list[tuple[int, int]]:
        """Returns list of (start_frame, end_frame) for each rally."""
        
        # 1. Ball activity signal
        ball_active = self._ball_activity(ball_positions)
        
        # 2. Player motion signal
        player_motion = self._player_motion(player_positions, frame_count)
        
        # 3. Combine signals
        combined = self._fuse_signals(ball_active, player_motion)
        
        # 4. Extract rally segments
        rallies = self._extract_segments(combined)
        
        return rallies
```

### LLM Enhancement (hybrid mode)
The LLM naturally segments rallies when analyzing frames. In the prompt, add:
- "Identify the start and end of each rally"
- "Note dead time between rallies"
- "A rally starts with a serve and ends when a point is scored"

## Files to Create/Modify
1. **Create** `src/analysis/rally_detector.py` — multi-signal rally detection
2. **Modify** `src/pipeline.py` — use RallyDetector instead of inline velocity checks
3. **Modify** `modal_app.py` — pass rally boundaries to stats computation
4. **Modify** `src/analysis/stats.py` — store rally timestamps for timeline markers

## Testing
- Long videos with lots of dead time between rallies
- Videos where ball detection is spotty
- Videos with warm-up/practice shots before the game
- Multiple games in one video (future: auto-split)
