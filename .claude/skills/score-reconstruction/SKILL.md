# Score Reconstruction

## Context
PB Vision reconstructs the score from video. We don't yet. This is critical for credibility.

## How Pickleball Scoring Works

### Sideout Scoring (Standard)
- Only the serving team can score
- Games to 11 (or 15), win by 2
- In doubles: each team member serves before side out (except first serve of game)
- Score format: serving team score – receiving team score – server number (1 or 2)

### Rally Scoring (APAC markets — PB Vision doesn't support this!)
- Either team can score on any rally
- Games to 21, win by 2
- Simpler to track — every rally = 1 point to winner

## Implementation Plan

### Step 1: Server Detection
**File:** New `src/analysis/server_detector.py`

Detect who is serving each rally:
- Serve is always shot #1 in a rally (we already classify this)
- Server position: behind baseline, hitting first shot
- In doubles: server alternates between team members
- Track server sequence to validate scoring

Inputs needed:
- `shot.shot_type == ShotType.SERVE` 
- `shot.player_id` and `shot.team`
- Player position (must be behind baseline)

### Step 2: Point Attribution
For each rally, determine which team won:
- Last shot in rally + outcome:
  - `ShotOutcome.ERROR` → other team wins point
  - `ShotOutcome.OUT` → other team wins point  
  - `ShotOutcome.NET` → other team wins point
  - `ShotOutcome.WINNER` → hitting team wins point
- If outcome unknown: use ball trajectory (did it land in/out?)

### Step 3: Score Tracking
**File:** New `src/analysis/score_tracker.py`

```python
@dataclass
class GameScore:
    team_0_score: int = 0
    team_1_score: int = 0
    serving_team: int = 0
    server_number: int = 1  # 1 or 2 (doubles)
    score_history: list[dict]  # per-rally score state
    
    def point_scored(self, winning_team: int, scoring_mode: str = "sideout"):
        if scoring_mode == "rally":
            # Either team scores
            ...
        else:
            # Only serving team scores, otherwise side out
            ...
```

### Step 4: LLM Enhancement (hybrid mode)
Add to LLM prompt: "Also identify which team won each rally and why (winner, error, out, net)."

The LLM already returns `point_winner` and `ending_type` per rally — wire this into the score tracker.

### Step 5: Score Display
- Add score progression chart to frontend (already have `score_progression` in MatchStats)
- Scoreboard overlay on video timeline
- Per-rally score state in rally log

## Files to Create/Modify
1. **Create** `src/analysis/server_detector.py` — detect serving player per rally
2. **Create** `src/analysis/score_tracker.py` — track score state
3. **Modify** `src/analysis/stats.py` — add score fields to MatchStats
4. **Modify** `src/pipeline.py` — wire score tracking into pipeline
5. **Modify** `modal_app.py` — update compute_stats to include scoring
6. **Modify** `frontend/components/StatsPanel.tsx` — score display

## Edge Cases
- First rally of game: only 1 server (not 2)
- Timeouts / side switches at specific scores
- Win by 2 rule
- Games to 11 vs 15 (should be configurable)
- Rally scoring vs sideout (should be configurable)

## PB Vision's Approach (from research)
- Uses server identification + serve order as primary signal
- Line calls as secondary (low confidence)
- Reconstructs "plausible scoring sequence with minimal corrections"
- Known to be off by a rally or two
- Only final score can be manually corrected
