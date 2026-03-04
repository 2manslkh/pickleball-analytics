# Error Classification (Forced vs Unforced)

## Context
PB Vision differentiates forced vs unforced errors with location data. We only count total errors. Error classification is critical for player improvement — unforced errors are the #1 thing intermediate players need to fix.

## Definitions

**Unforced Error:** Player makes a mistake on a shot they "should" have made. The opponent's previous shot was not particularly difficult.
- Hit into the net on a routine dink
- Hit a serve out when not under pressure
- Popped up a ball they had time to handle

**Forced Error:** Player makes a mistake because the opponent's shot was excellent.
- Opponent hit a winner-quality drive, player got a paddle on it but hit it out
- Opponent hit a perfect drop, player had to reach and hit into net
- High-speed ball with little reaction time

**Winner:** Shot that the opponent couldn't reach at all (not an error, but related).

## Classification Logic

### Heuristic Approach (CV-only mode)

For the shot that resulted in an error (out/net), look at the **previous shot**:

```python
def classify_error(error_shot: Shot, previous_shot: Shot) -> str:
    """Returns 'unforced_error', 'forced_error', or 'winner'."""
    
    # If previous shot was high speed → likely forced
    if previous_shot.ball_speed > DRIVE_SPEED_THRESHOLD:
        return "forced_error"
    
    # If previous shot was in kitchen zone and slow → unforced (routine shot)
    if previous_shot.zone in ("near_kitchen", "far_kitchen") and previous_shot.ball_speed < DINK_SPEED:
        return "unforced_error"
    
    # If error player was in good position (kitchen) → unforced
    if error_shot.zone in ("near_kitchen", "far_kitchen"):
        return "unforced_error"
    
    # If error player was stretched (far from ball) → forced
    if player_ball_distance > STRETCH_THRESHOLD:
        return "forced_error"
    
    # Default: unforced (conservative — assume player should make routine shots)
    return "unforced_error"
```

### LLM Approach (hybrid mode)
Add to prompt: "For each point-ending error, classify as 'unforced_error' (mistake on a makeable shot) or 'forced_error' (opponent's great shot caused the error). Consider the previous shot's difficulty."

### Error Type Sub-Classification
- **Net error**: ball hit into net
- **Out error**: ball hit past baseline or sideline  
- **Pop-up**: ball hit too high, giving opponent easy smash opportunity

Detection:
- Net error: ball Y near NET_POSITION, ball stops (velocity → 0)
- Out error: ball lands outside court bounds (court_pos outside 0-20, 0-44)
- Pop-up: ball trajectory goes high (vy strongly negative = upward), then opponent hits overhead

## Stats to Track

Per player:
```python
class ErrorStats(BaseModel):
    total_errors: int
    unforced_errors: int
    forced_errors: int
    net_errors: int
    out_errors: int
    popups: int
    error_rate: float  # errors / total_shots %
    unforced_error_rate: float
    # By shot type
    errors_by_type: dict[str, int]  # {"dink": 3, "drive": 2, ...}
```

## Files to Modify
1. `src/analysis/shot_classifier.py` — add error classification logic, error type enum
2. `src/analysis/llm_classifier.py` — update prompt for error classification
3. `src/analysis/stats.py` — add ErrorStats to PlayerStats
4. `src/pipeline.py` — wire error classification after rally ends
5. `frontend/components/StatsPanel.tsx` — error breakdown display
