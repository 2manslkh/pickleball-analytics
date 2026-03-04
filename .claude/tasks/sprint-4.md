# Sprint 4: Polish & Growth (Weeks 7-8)

## Goal
User experience, retention, and viral features.

## Tasks

### Task 4.1: User Accounts + Game History
**Files:** New auth system, new DB schema, frontend auth flow
**Acceptance:**
- [ ] User signup/login (email or Google OAuth)
- [ ] Analysis results saved to user account
- [ ] Game history list view (all past analyses)
- [ ] Delete/archive games
- [ ] Storage: Supabase or Firebase

### Task 4.2: Cross-Game Trends ("Me" Page)
**Depends on:** Task 4.1 (user accounts)
**Files:** New `frontend/app/me/page.tsx`, new API endpoint
**Acceptance:**
- [ ] Aggregate stats across all user's games
- [ ] Line charts: accuracy, error rate, kitchen time over time
- [ ] Per-shot-type trend tracking
- [ ] "Improving" / "declining" indicators per metric
- [ ] Date range filter

### Task 4.3: Highlight Auto-Detection
**Files:** New `src/analysis/highlight_detector.py`, modify stats
**Acceptance:**
- [ ] Detect notable moments: Erne, ATP, long rallies (10+ shots), firefights (rapid exchanges), aces
- [ ] Each highlight tagged with type, frame range, and confidence
- [ ] Frontend: highlights section with click-to-seek
- [ ] Highlight thumbnails (extract frame at highlight moment)

### Task 4.4: Reel Creator
**Depends on:** Task 4.3 (highlights)
**Files:** New `src/export/reel_creator.py`, new frontend component
**Acceptance:**
- [ ] Select highlights to include in reel
- [ ] Auto-crop for vertical (9:16) or square (1:1) for social
- [ ] ffmpeg-based clip extraction + concatenation
- [ ] Add transition effects between clips
- [ ] Export as MP4
- [ ] Download button in frontend

### Task 4.5: Skill Rating System
**Files:** New `src/analysis/skill_rating.py`, modify stats
**Acceptance:**
- [ ] 6 dimensions: Serve, Return, Offense, Defense, Agility, Consistency
- [ ] Scale: 2.0-8.0 (DUPR-aligned)
- [ ] Per-game rating calculated from shot stats
- [ ] Aggregate rating from recent games (weighted)
- [ ] Frontend: radar chart showing 6 dimensions
- [ ] Frontend: overall rating number

## Dependencies
- Task 4.1 is foundational — blocks 4.2
- Task 4.3 blocks 4.4
- Task 4.5 is independent
- All tasks can start after Sprint 3 core work
