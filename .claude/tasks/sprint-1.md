# Sprint 1: Core Analysis Quality (Weeks 1-2)

## Goal
Match PB Vision's analysis depth so output is credible.

## Tasks

### Task 1.1: Expand Shot Types
**Skills:** `.claude/skills/shot-classification/SKILL.md`
**Files:** `src/analysis/shot_classifier.py`, `src/analysis/llm_classifier.py`, `src/analysis/stats.py`
**Acceptance:**
- [ ] ShotType enum includes: erne, atp, reset, speedup, passing, poach
- [ ] Heuristic classifier has rules for each new type
- [ ] LLM prompt updated with all new types
- [ ] PlayerStats model has count fields for each new type
- [ ] Frontend displays all shot types with distinct colors

### Task 1.2: Improve Rally Detection
**Skills:** `.claude/skills/rally-detection/SKILL.md`
**Files:** New `src/analysis/rally_detector.py`, modify `src/pipeline.py`
**Acceptance:**
- [ ] RallyDetector class uses ball activity + player motion signals
- [ ] Pipeline uses RallyDetector instead of inline velocity checks
- [ ] Dead time between rallies correctly identified
- [ ] Rally boundaries stored with frame timestamps
- [ ] False rally rate < 10% on test videos

### Task 1.3: Score Reconstruction
**Skills:** `.claude/skills/score-reconstruction/SKILL.md`
**Files:** New `src/analysis/server_detector.py`, new `src/analysis/score_tracker.py`, modify `src/analysis/stats.py`
**Acceptance:**
- [ ] Server detected per rally (which player served)
- [ ] Points attributed to correct team per rally
- [ ] Running score tracked (sideout scoring)
- [ ] Score progression in MatchStats is accurate
- [ ] Frontend shows score state per rally in rally log

### Task 1.4: Court Coverage Heatmap
**Skills:** `.claude/skills/heatmap-visualization/SKILL.md`
**Files:** New `src/analysis/heatmap.py`, new `frontend/components/CourtHeatmap.tsx`, modify `src/pipeline.py`
**Acceptance:**
- [ ] Raw court (x,y) positions collected during CV pass
- [ ] 2D histogram generated per player
- [ ] SVG court component with heatmap overlay
- [ ] Heatmap visible per player in stats panel
- [ ] Court lines, kitchen, net accurately drawn

### Task 1.5: Ball Speed Calibration
**Skills:** `.claude/skills/speed-calibration/SKILL.md`
**Files:** `src/analysis/shot_classifier.py`, `src/analysis/stats.py`, `src/pipeline.py`
**Acceptance:**
- [ ] Ball speed converted from px/frame to mph using homography
- [ ] Speed smoothed over 3-frame window
- [ ] Both peak and average speed reported per shot
- [ ] Per-shot-type speed stats in PlayerStats (median, max)
- [ ] Speeds in realistic ranges (dink 5-15mph, drive 25-50mph)
- [ ] Frontend displays speed in mph

## Dependencies
- Tasks 1.1-1.5 are independent and can run in parallel
- All tasks modify `stats.py` — merge carefully
- Task 1.4 depends on court detection working (has fallback if it doesn't)
- Task 1.5 depends on court detection for calibration
