# Task Tracker

## How This Works
When asked to "work on the next task", find the first task with status `ready` below, change it to `in_progress`, and execute it. When done, mark it `done` and update this file.

Read these before starting any task:
1. `/CLAUDE.md` — project context
2. The skill file(s) listed in the task
3. The sprint file for full acceptance criteria

## Current Sprint: 1 — Core Analysis Quality

### Task 1.1: Expand Shot Types
- **Status:** `done`
- **Skill:** `.claude/skills/shot-classification/SKILL.md`
- **Sprint:** `.claude/tasks/sprint-1.md`
- **Files:** `src/analysis/shot_classifier.py`, `src/analysis/llm_classifier.py`, `src/analysis/stats.py`, `frontend/components/StatsPanel.tsx`, `frontend/components/VideoPlayer.tsx`
- **Summary:** Add erne, atp, reset, speedup, passing, poach to ShotType enum. Update heuristic rules, LLM prompt, stats model, and frontend colors/display.

### Task 1.2: Improve Rally Detection
- **Status:** `ready`
- **Skill:** `.claude/skills/rally-detection/SKILL.md`
- **Sprint:** `.claude/tasks/sprint-1.md`
- **Files:** New `src/analysis/rally_detector.py`, `src/pipeline.py`
- **Summary:** Replace inline velocity-based rally detection with multi-signal RallyDetector (ball activity + player motion + serve detection).

### Task 1.3: Score Reconstruction
- **Status:** `ready`
- **Skill:** `.claude/skills/score-reconstruction/SKILL.md`
- **Sprint:** `.claude/tasks/sprint-1.md`
- **Files:** New `src/analysis/server_detector.py`, new `src/analysis/score_tracker.py`, `src/analysis/stats.py`, `src/pipeline.py`
- **Summary:** Detect server per rally, attribute points, track running score (sideout scoring), wire into MatchStats.

### Task 1.4: Court Coverage Heatmap
- **Status:** `ready`
- **Skill:** `.claude/skills/heatmap-visualization/SKILL.md`
- **Sprint:** `.claude/tasks/sprint-1.md`
- **Files:** New `src/analysis/heatmap.py`, new `frontend/components/CourtHeatmap.tsx`, `src/pipeline.py`, `src/analysis/stats.py`
- **Summary:** Collect raw court (x,y) positions during CV pass. Generate 2D histogram. SVG court with heatmap overlay in frontend.

### Task 1.5: Ball Speed Calibration
- **Status:** `ready`
- **Skill:** `.claude/skills/speed-calibration/SKILL.md`
- **Sprint:** `.claude/tasks/sprint-1.md`
- **Files:** `src/analysis/shot_classifier.py`, `src/analysis/stats.py`, `src/pipeline.py`, `frontend/components/StatsPanel.tsx`
- **Summary:** Convert ball speed from px/frame to mph using court homography. Smooth over 3 frames. Report peak + avg speed per shot type.

---

## Sprint 2 — Stats & Visualization

### Task 2.1: Serve/Return Depth Analysis
- **Status:** `blocked` (waiting for Sprint 1)
- **Sprint:** `.claude/tasks/sprint-2.md`

### Task 2.2: Kitchen Arrival Tracking
- **Status:** `blocked`
- **Sprint:** `.claude/tasks/sprint-2.md`

### Task 2.3: Error Classification
- **Status:** `blocked`
- **Skill:** `.claude/skills/error-classification/SKILL.md`
- **Sprint:** `.claude/tasks/sprint-2.md`

### Task 2.4: Shot Quality Model
- **Status:** `blocked`
- **Sprint:** `.claude/tasks/sprint-2.md`

### Task 2.5: 3rd Shot Drop Deep Analysis
- **Status:** `blocked`
- **Sprint:** `.claude/tasks/sprint-2.md`

### Task 2.6: Per-Shot-Type Speed Stats
- **Status:** `blocked`
- **Sprint:** `.claude/tasks/sprint-2.md`

---

## Sprint 3 — Differentiators

### Task 3.1: Drill Mode
- **Status:** `blocked`
- **Skill:** `.claude/skills/drill-mode/SKILL.md`
- **Sprint:** `.claude/tasks/sprint-3.md`

### Task 3.2: Rally Scoring Support
- **Status:** `blocked`
- **Sprint:** `.claude/tasks/sprint-3.md`

### Task 3.3: Open Public API + Docs
- **Status:** `blocked`
- **Sprint:** `.claude/tasks/sprint-3.md`

### Task 3.4: Shareable Results Page
- **Status:** `blocked`
- **Sprint:** `.claude/tasks/sprint-3.md`

---

## Sprint 4 — Polish & Growth

### Task 4.1: User Accounts + Game History
- **Status:** `blocked`
- **Sprint:** `.claude/tasks/sprint-4.md`

### Task 4.2: Cross-Game Trends
- **Status:** `blocked`
- **Sprint:** `.claude/tasks/sprint-4.md`

### Task 4.3: Highlight Auto-Detection
- **Status:** `blocked`
- **Sprint:** `.claude/tasks/sprint-4.md`

### Task 4.4: Reel Creator
- **Status:** `blocked`
- **Sprint:** `.claude/tasks/sprint-4.md`

### Task 4.5: Skill Rating System
- **Status:** `blocked`
- **Sprint:** `.claude/tasks/sprint-4.md`
