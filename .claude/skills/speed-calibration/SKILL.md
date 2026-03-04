# Ball Speed Calibration

## Context
We track ball speed in pixels/frame. Need to convert to real-world mph for meaningful stats. PB Vision reports median speed per shot type with percentile comparisons.

## Approach

We already have court homography mapping (image pixels → court feet). Use this to convert ball velocity from px/frame to ft/s → mph.

### Conversion Pipeline

```python
# 1. Ball displacement in image pixels
dx_px = ball_pos[t].x - ball_pos[t-1].x
dy_px = ball_pos[t].y - ball_pos[t-1].y

# 2. Map both positions to court coordinates (feet)
court_pos_t = court_mapping.image_to_court(ball_pos[t])
court_pos_prev = court_mapping.image_to_court(ball_pos[t-1])

# 3. Displacement in feet
dx_ft = court_pos_t[0] - court_pos_prev[0]
dy_ft = court_pos_t[1] - court_pos_prev[1]
displacement_ft = sqrt(dx_ft² + dy_ft²)

# 4. Time between frames
dt_seconds = 1.0 / fps  # e.g., 1/30 = 0.033s

# 5. Speed in ft/s → mph
speed_fps = displacement_ft / dt_seconds
speed_mph = speed_fps * 0.6818  # ft/s to mph
```

### Smoothing
Raw frame-to-frame speed is noisy. Use rolling average over 3-5 frames:
```python
speeds = [compute_speed(t) for t in range(len(positions)-1)]
smoothed = np.convolve(speeds, np.ones(3)/3, mode='valid')
```

### Report Both
- **Peak speed**: max smoothed speed during shot trajectory
- **Average speed**: mean across full shot trajectory (what PB Vision reports)

## Typical Pickleball Speeds (for validation)
- Dink: 5-15 mph
- Drop: 10-25 mph
- Drive: 25-50 mph
- Serve: 30-55 mph
- Smash/overhead: 40-65 mph

If our calibrated speeds are way off these ranges, the homography is likely wrong.

## Files to Modify
1. `src/analysis/shot_classifier.py` — add `speed_mph` field to Shot
2. `src/analysis/stats.py` — add speed stats (median, max) per shot type to PlayerStats
3. `src/pipeline.py` — compute calibrated speed during shot detection
4. `src/court/court_detector.py` — may need to expose pixel-to-feet scale factor
5. `frontend/components/StatsPanel.tsx` — display speed in mph

## Dependencies
- Court homography must be valid (court detected successfully)
- If court not detected, fall back to pixel speed with disclaimer
- fps must be accurate (read from video metadata)
