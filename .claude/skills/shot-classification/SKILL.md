# Shot Classification

## Context
Shot classification is the core intelligence of the analysis pipeline. Currently we support 8 shot types. PB Vision supports 15+. We need parity.

## Current Shot Types
Defined in `src/analysis/shot_classifier.py` as `ShotType` enum:
- `serve`, `return`, `dink`, `drive`, `drop`, `lob`, `volley`, `overhead`, `unknown`

## Shot Types to Add

### Erne
- Player jumps/runs around the kitchen to volley at the net post
- Detection cues: player position far outside sideline + volley near net
- Court position: X < -1 or X > COURT_WIDTH + 1, Y near NET_POSITION

### ATP (Around The Post)
- Ball travels around the net post (not over it)
- Detection cues: ball trajectory passes outside the net post area
- Court position: ball X goes outside court bounds, then lands in

### Reset
- Soft shot from mid-court/baseline intended to neutralize and get to kitchen
- Detection cues: medium speed, from transition/baseline zone, lands in kitchen
- Differentiate from drop: reset is defensive (response to pressure), drop is offensive (3rd shot)

### Speedup
- Sudden hard shot during a dink rally — attempt to catch opponent off guard
- Detection cues: dink rally (slow shots) → sudden speed spike
- Context: must follow 2+ dinks in the rally

### Passing Shot
- Shot aimed to pass an opponent at the net
- Detection cues: fast shot aimed down the sideline, opponent near kitchen
- Court position: ball trajectory parallel to sideline

### Poach
- Player crosses to partner's side to intercept a shot
- Detection cues: player X position crosses court midline (X=10ft)
- Must be at kitchen line, intercepting a ball aimed at partner

## Files to Modify
1. `src/analysis/shot_classifier.py` — Add enums + heuristic rules
2. `src/analysis/llm_classifier.py` — Update ANALYSIS_PROMPT to include new shot types
3. `src/analysis/stats.py` — Add fields to PlayerStats model
4. `frontend/components/StatsPanel.tsx` — Add UI for new shot types
5. `frontend/components/VideoPlayer.tsx` — Add colors for new shot types

## Heuristic Classification Rules (CV-only mode)

The classifier in `shot_classifier.py` uses:
- `ball_speed` (pixels/frame)
- `vx`, `vy` (ball velocity components)
- `zone` (court zone from homography)
- `shot_number` in rally (1=serve, 2=return, 3=third shot)
- Player position relative to court

### Speed Thresholds (current, may need calibration)
- Dink: speed ≤ 5.0 px/frame
- Drive: speed ≥ 12.0 px/frame
- Lob: vertical velocity < -8.0 (upward)

## LLM Prompt Updates (hybrid mode)

The prompt in `llm_classifier.py` tells the LLM what shot types to identify. Update the `ANALYSIS_PROMPT` and the `shot_type` field description to include all new types.

## Testing
- Test with sample videos at different skill levels
- Erne/ATP are rare — may need specific test clips
- Speedup detection depends on rally context (needs dink sequence first)
