# Court Heatmap & Spatial Visualization

## Context
PB Vision has court coverage heatmaps, serve/return depth charts, and shot placement visualizations. We have the underlying zone data but no visual output.

## What We Have
- `court_detector.py` maps image coords → court coords (feet)
- `StatsAggregator` tracks zone observations per player: `{player_id: ["near_kitchen", "near_kitchen", "near_transition", ...]}`
- `PlayerStats` has `kitchen_time_pct`, `transition_time_pct`, `baseline_time_pct`
- Court dimensions: 20ft × 44ft, kitchen 7ft from net

## What to Build

### 1. Court Coverage Heatmap
**Per player**, show where they spent time on court.

Backend (`src/analysis/heatmap.py`):
```python
def generate_heatmap(positions: list[tuple[float, float]], court_width=20, court_length=44) -> np.ndarray:
    """Generate 2D histogram of player positions mapped to court coords.
    Returns a normalized grid (e.g., 20×44 or 40×88 for half-foot resolution).
    """
```

Frontend component: `frontend/components/CourtHeatmap.tsx`
- SVG court diagram (top-down view)
- Color gradient overlay (blue=cold, red=hot)
- Court lines drawn: baseline, sidelines, kitchen line, centerline, net
- Toggle per player

### 2. Serve Placement Chart
Where serves land on the receiving side.

Data needed: court position of ball at first bounce after serve.
- Group by: deep/mid/short × left/center/right (3×3 grid)
- Show count + percentage in each zone

### 3. Return Depth Chart
Same as serve placement but for return shots.

### 4. Shot Placement Distribution
For any shot type, show where it lands:
- Left/center/right distribution
- Deep/mid/short distribution
- Per player and per team

### 5. Kitchen Arrival Tracking
Per rally, did the player reach the kitchen line before the ball came back?
- Binary: arrived / didn't arrive
- Time to arrival (frames from serve/return to reaching kitchen zone)
- Percentage across all rallies

## Data Pipeline

Currently `pipeline.py` tracks zones as strings. For heatmaps we need actual (x, y) court coordinates:

In `_run_cv_pass` or `_analyze_cv_only`, after `court_mapping.image_to_court()`:
```python
# Already computing this:
court_pos = court_mapping.image_to_court(player.last_position)
zone = court_mapping.get_zone(court_pos)

# Also store raw position:
position_history[player.tracker_id].append(court_pos)
```

Add `position_history: dict[int, list[tuple[float, float]]]` to cv_data output.

## Frontend Implementation

Court SVG dimensions: scale court (20×44ft) to viewport.

```tsx
// Court component with overlaid heatmap
<svg viewBox="0 0 200 440">
  {/* Court lines */}
  <rect x="0" y="0" width="200" height="440" stroke="white" fill="none" />
  <line x1="0" y1="220" x2="200" y2="220" stroke="white" /> {/* Net */}
  <line x1="0" y1="150" x2="200" y2="150" stroke="white" /> {/* Near kitchen */}
  <line x1="0" y1="290" x2="200" y2="290" stroke="white" /> {/* Far kitchen */}
  
  {/* Heatmap overlay */}
  {heatmapCells.map(cell => (
    <rect x={cell.x} y={cell.y} width={cellW} height={cellH} 
          fill={`rgba(255,0,0,${cell.intensity})`} />
  ))}
</svg>
```

## Files to Create/Modify
1. **Create** `src/analysis/heatmap.py` — generate heatmap grid from position history
2. **Modify** `src/pipeline.py` — collect raw court positions (not just zones)
3. **Modify** `src/analysis/stats.py` — add position_history to MatchStats or separate endpoint
4. **Modify** `modal_app.py` — pass position data through
5. **Create** `frontend/components/CourtHeatmap.tsx` — SVG court + heatmap overlay
6. **Create** `frontend/components/ServePlacement.tsx` — serve landing zones
7. **Modify** `frontend/components/StatsPanel.tsx` — integrate new visualizations
