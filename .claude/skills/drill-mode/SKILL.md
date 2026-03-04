# Drill Mode (PB Vision's #1 Gap)

## Context
PB Vision's most requested feature (97 votes) is drill/practice analysis. They only support full games. This is our biggest differentiation opportunity.

## What Drill Mode Means

Players practice specific shots outside of games:
- **Serving practice** — repeated serves, no rally
- **Dink rallies** — two players at kitchen, dinking back and forth
- **3rd shot drop drills** — one player drives, other practices drops
- **Ball machine** — player hits against a machine
- **Partner drills** — structured practice patterns

## How It Differs from Game Analysis

| Aspect | Game Mode | Drill Mode |
|--------|-----------|------------|
| Rally structure | Serve → rally → point | Continuous or repeated patterns |
| Scoring | Points tracked | Reps tracked |
| Players | 2 or 4 | 1-4 |
| Court usage | Full court | May use half court |
| Key metrics | Win%, errors, strategy | Consistency, accuracy, improvement over reps |

## Implementation Plan

### Step 1: Drill Detection
Detect whether a video is a game or a drill:
- No serve sequence → likely drill
- Same shot type repeated → likely drill
- Players staying in same zone → likely drill
- Only 1-2 players visible → likely drill

Or: user selects mode on upload (simpler for MVP).

### Step 2: Drill Types & Metrics

**Serving Practice:**
- Rep count (number of serves)
- In/out/net percentage
- Speed distribution
- Placement distribution (zones)
- Consistency score (standard deviation of placement)

**Dink Rallies:**
- Rally length (continuous dink count)
- Longest streak
- Net errors
- Placement variety
- Tempo (time between shots)

**3rd Shot Drop Practice:**
- Rep count
- Success rate (landed in kitchen)
- Quality distribution
- Height over net (lower = better)
- Depth (closer to net = better)

**Ball Machine:**
- Shot count
- Shot type distribution
- Consistency metrics
- Fatigue analysis (accuracy over time)

### Step 3: Stats Model

**File:** `src/analysis/drill_stats.py`

```python
class DrillStats(BaseModel):
    drill_type: str  # "serve", "dink_rally", "third_shot_drop", "ball_machine", "free_practice"
    total_reps: int
    duration_seconds: float
    
    # Consistency metrics
    accuracy_pct: float          # % of shots landing in target zone
    consistency_score: float     # 0-100, lower variance = higher
    
    # Per-rep data
    reps: list[DrillRep]
    
    # Improvement tracking
    first_half_accuracy: float
    second_half_accuracy: float
    improving: bool              # Did accuracy improve over the session?

class DrillRep(BaseModel):
    frame_idx: int
    shot_type: str
    outcome: str       # in, out, net
    speed: float
    placement: tuple[float, float]  # court coords
    quality: float     # 0-1
```

### Step 4: Pipeline Changes

In `AnalysisPipeline`:
```python
def analyze(self, video_path, mode="game"):  # Add mode param
    if mode == "drill":
        return self._analyze_drill(video_path)
    else:
        return self._analyze_game(video_path)  # existing logic
```

Drill analysis is simpler:
1. CV pass (same: detect players, ball, court)
2. No rally segmentation needed — each shot is a rep
3. Classify each shot, track placement/speed/outcome
4. Compute consistency metrics

### Step 5: Frontend

New drill results view:
- Rep counter with success/fail markers
- Accuracy over time line chart (shows improvement)
- Placement scatter plot on court diagram
- Speed histogram
- Consistency score

## Files to Create/Modify
1. **Create** `src/analysis/drill_stats.py` — drill-specific stats model
2. **Create** `src/analysis/drill_detector.py` — auto-detect drill vs game
3. **Modify** `src/pipeline.py` — add `_analyze_drill()` method
4. **Modify** `modal_app.py` — add drill mode to API
5. **Modify** `src/main.py` — `--drill` flag
6. **Create** `frontend/components/DrillResults.tsx` — drill results UI
7. **Modify** `frontend/components/UploadZone.tsx` — game/drill toggle
8. **Modify** `frontend/app/page.tsx` — route to drill results

## API Changes
```json
POST /analyze
{
  "url": "https://youtube.com/...",
  "mode": "cv",
  "video_type": "drill",    // NEW: "game" or "drill"
  "drill_type": "serve",    // optional: hint for auto-detection
  "max_seconds": 60
}
```
