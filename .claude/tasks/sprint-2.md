# Sprint 2: Stats & Visualization (Weeks 3-4)

## Goal
Dashboard matches PB Vision's stats breadth.

## Tasks

### Task 2.1: Serve/Return Depth Analysis
**Files:** `src/analysis/stats.py`, `src/pipeline.py`, new `frontend/components/ServePlacement.tsx`
**Acceptance:**
- [ ] Track where serves land (court coords of first bounce)
- [ ] Classify into zones: deep/mid/short × left/center/right
- [ ] Same for returns
- [ ] Frontend: 3×3 grid on court SVG showing counts + percentages
- [ ] Per-player breakdown

### Task 2.2: Kitchen Arrival Tracking
**Files:** `src/analysis/stats.py`, `src/pipeline.py`
**Acceptance:**
- [ ] Per rally: did player reach kitchen zone within N frames of serve/return?
- [ ] Kitchen arrival percentage in PlayerStats
- [ ] Time-to-kitchen metric (avg frames to reach kitchen after serving/returning)
- [ ] Frontend displays kitchen arrival % prominently

### Task 2.3: Error Classification (Forced vs Unforced)
**Skills:** `.claude/skills/error-classification/SKILL.md`
**Files:** `src/analysis/shot_classifier.py`, `src/analysis/llm_classifier.py`, `src/analysis/stats.py`
**Acceptance:**
- [ ] Errors classified as forced/unforced using previous shot context
- [ ] Sub-classified by type: net, out, popup
- [ ] LLM prompt asks for error classification
- [ ] PlayerStats includes forced_errors, unforced_errors, net_errors, out_errors
- [ ] Frontend error breakdown section in player cards

### Task 2.4: Shot Quality Model
**Files:** `src/analysis/shot_classifier.py`, `src/analysis/stats.py`
**Acceptance:**
- [ ] Dink quality: based on height above net + placement in kitchen
- [ ] Drive quality: based on speed + depth + height above net
- [ ] Drop quality: based on landing in kitchen + height above net
- [ ] Quality score 0-1 per shot
- [ ] Average quality per shot type in PlayerStats
- [ ] Frontend: quality indicator (green/yellow/red) or score

### Task 2.5: 3rd Shot Drop Deep Analysis
**Files:** `src/analysis/stats.py`, `frontend/components/StatsPanel.tsx`
**Acceptance:**
- [ ] FH vs BH 3rd shot drop breakdown (need paddle side detection or LLM)
- [ ] Success rate: % that landed in kitchen and didn't result in error
- [ ] Effectiveness: % of 3rd shot drops that led to winning the point
- [ ] Comparison: drop vs drive on 3rd shot (which is more effective for this player)
- [ ] Frontend: 3rd shot analysis section with comparison chart

### Task 2.6: Per-Shot-Type Speed Stats
**Depends on:** Sprint 1 Task 1.5 (speed calibration)
**Files:** `src/analysis/stats.py`, `frontend/components/StatsPanel.tsx`
**Acceptance:**
- [ ] Median and max speed per shot type per player
- [ ] Speed distribution data (for histogram/chart)
- [ ] Frontend: speed stats table or bar chart per player

## Dependencies
- Task 2.1, 2.2 depend on court detection
- Task 2.3 can run in parallel with everything
- Task 2.4 depends on court coords (height above net needs 3D estimation or approximation)
- Task 2.5, 2.6 extend existing stats — straightforward
