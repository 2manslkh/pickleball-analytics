# Feature Match Plan: Pickleball Analytics vs PB Vision

*Last updated: 2026-03-04*

## PB Vision Feature Inventory vs Our Status

### Legend
- ✅ We have it
- 🟡 Partial / in progress
- ❌ Not built yet
- 🔵 Our advantage (we do it better or differently)

---

## Phase 1: Core Parity (Must-Have for MVP Launch)

These are table-stakes features. Without them, nobody switches from PB Vision.

| # | Feature | PB Vision | Us | Priority | Effort |
|---|---------|-----------|-----|----------|--------|
| 1 | **Player Detection & Tracking** | ✅ Custom CV | ✅ YOLOv8 + ByteTrack | Done | — |
| 2 | **Ball Detection & Tracking** | ✅ Custom CV | ✅ YOLO + color fallback | Done | — |
| 3 | **Court Detection** | ✅ Auto | ✅ Hough + homography | Done | — |
| 4 | **Shot Classification** | ✅ serve/return/dink/drive/drop/lob/volley/smash/reset/Erne/ATP | 🟡 serve/return/dink/drive/drop/lob/volley/overhead | High | 1 week |
| 5 | **Rally Detection** | ✅ Auto | 🟡 Basic (velocity-based) | High | 3 days |
| 6 | **Score Reconstruction** | ✅ AI-based | ❌ | High | 1 week |
| 7 | **YouTube URL Input** | ❌ (upload only) | ✅ yt-dlp | Done | — |
| 8 | **Video Upload** | ✅ App + web | ✅ Web + API | Done | — |
| 9 | **Stats Dashboard** | ✅ Web + app | ✅ Web (Next.js) | Done | — |
| 10 | **Shot Counts by Type** | ✅ Per player | ✅ Per player | Done | — |
| 11 | **Dink Accuracy** | ✅ Quality rating | ✅ Kitchen landing % | Done | — |
| 12 | **3rd Shot Drop Analysis** | ✅ FH/BH %, effectiveness | 🟡 Count + success rate | Medium | 3 days |
| 13 | **Unforced Error Tracking** | ✅ Forced vs unforced + location | 🟡 Count only | High | 1 week |
| 14 | **Court Coverage Heatmap** | ✅ Visual heatmap | ❌ (have zone % data) | High | 3 days |
| 15 | **Kitchen Arrival %** | ✅ Per rally | ❌ | Medium | 3 days |
| 16 | **Serve/Return Depth** | ✅ Zone breakdown | ❌ | Medium | 3 days |
| 17 | **Shot Speed** | ✅ Median mph + percentile | ❌ (have px/frame speed) | Medium | 1 week |
| 18 | **Team Assignment** | ✅ Auto | ✅ Auto (Y-position) | Done | — |
| 19 | **Video Playback + Timeline** | ✅ Custom player | ✅ w/ shot markers | Done | — |

**Phase 1 Effort Estimate: ~4-5 weeks**

---

## Phase 2: Competitive Differentiators (What Makes Us Better)

Features where we can leapfrog PB Vision.

| # | Feature | PB Vision | Our Approach | Advantage | Effort |
|---|---------|-----------|--------------|-----------|--------|
| 20 | **Processing Speed** | 30 min – 24 hrs | 🔵 ~1-2 min (GPU on Modal) | **Massive** — instant gratification vs waiting hours | Done |
| 21 | **YouTube Analysis** | ❌ Must upload | 🔵 Paste any YouTube link | **Unique** — analyze pro matches, learn from the best | Done |
| 22 | **AI Observations** | AI Coach (Premium only) | 🔵 Included in hybrid mode | Strategic insights in every analysis | Done |
| 23 | **Pricing** | $100-400/yr + video minutes | 🔵 ~$0.05-0.10/video (pay per use) | **10-50x cheaper**, no subscription anxiety | Done |
| 24 | **CV-Only Mode** | ❌ Cloud only | 🔵 Free, offline, instant | Zero cost option for basic stats | Done |
| 25 | **Drill Support** | ❌ (97 votes requesting!) | ❌ Build this | Their #1 requested feature, huge gap | 2 weeks |
| 26 | **Rally Scoring** | ❌ (sideout only) | ❌ Build this | Unlocks Asia-Pacific market | 1 week |
| 27 | **Real-time Analysis** | ❌ Post-game only | ❌ Future (stream frames to API) | Game-changing for live play | 4 weeks |
| 28 | **Multi-Camera** | ❌ Single angle only | ❌ Future | Better accuracy, more angles | 6 weeks |
| 29 | **Open API** | Partner-only ($8/hr) | 🔵 Open API on Modal | Developer-friendly, build ecosystem | 1 week |

---

## Phase 3: Feature Parity (Nice to Have)

Match PB Vision's full feature set.

| # | Feature | PB Vision | Us | Effort |
|---|---------|-----------|-----|--------|
| 30 | **Skill Rating (2.0-8.0)** | ✅ 6 dimensions, caps at 5.5 | ❌ | 2 weeks |
| 31 | **3D Shot Trajectory** | ✅ Interactive viz | ❌ | 2 weeks |
| 32 | **Shot Explorer (filter/search)** | ✅ Presets, cross-game | ❌ | 1 week |
| 33 | **Shot Quality Assessment** | ✅ Green/red rating | ❌ | 1 week |
| 34 | **Highlights Auto-Detection** | ✅ ATPs, Ernes, firefights | ❌ | 1 week |
| 35 | **Scoreboard Overlay** | ✅ On video | ❌ | 3 days |
| 36 | **Cross-Game Trends** | ✅ "Me" page | ❌ (need user accounts + DB) | 3 weeks |
| 37 | **Friend Tagging** | ✅ Viral growth | ❌ | 2 weeks |
| 38 | **Reel Creator** | 🟡 In progress | ❌ | 2 weeks |
| 39 | **Data Export (JSON/CSV)** | ✅ 3 tiers | 🟡 JSON output | 2 days |
| 40 | **Mobile App** | ✅ iOS + Android | ❌ | 8 weeks |
| 41 | **Stacking Analysis** | ✅ Left/right side % | ❌ | 3 days |
| 42 | **Left-Handed Support** | ❌ (requested) | ❌ | 3 days |
| 43 | **EDL Export** (video editing) | ✅ | ❌ | 2 days |

---

## Roadmap: Recommended Build Order

### Sprint 1 (Weeks 1-2): Core Analysis Quality
**Goal:** Match PB Vision's analysis depth so output is credible.

- [ ] Expand shot types: add Erne, ATP, reset, speedup, passing shot
- [ ] Improve rally detection: use ball + player positions, not just velocity
- [ ] Score reconstruction: server detection → sideout scoring logic
- [ ] Court coverage heatmap visualization
- [ ] Calibrate ball speed to real-world mph (using court dimensions)

### Sprint 2 (Weeks 3-4): Stats & Visualization
**Goal:** Dashboard matches PB Vision's stats breadth.

- [ ] Serve/return depth charts
- [ ] Kitchen arrival tracking
- [ ] Unforced vs forced error classification
- [ ] Shot quality model (height above net, depth, placement)
- [ ] Improve 3rd shot drop analysis (FH/BH, effectiveness)
- [ ] Per-shot-type speed stats

### Sprint 3 (Weeks 5-6): Differentiators
**Goal:** Ship features PB Vision doesn't have.

- [ ] **Drill mode** — analyze practice sessions, not just games (their #1 gap)
- [ ] **Rally scoring** support (unlock APAC market)
- [ ] Open public API with documentation
- [ ] Shareable results page (unique URL per analysis)

### Sprint 4 (Weeks 7-8): Polish & Growth
**Goal:** User experience and viral features.

- [ ] User accounts + game history
- [ ] Cross-game trends ("Me" page)
- [ ] Highlight auto-detection (Erne, ATP, long rallies)
- [ ] Reel creator (auto-edit highlights for social)
- [ ] Skill rating system (6 dimensions)

### Future (Month 3+)
- [ ] Mobile app (React Native)
- [ ] Real-time streaming analysis
- [ ] Friend tagging + social features
- [ ] 3D shot trajectory visualization
- [ ] Multi-camera fusion
- [ ] Coaching marketplace
- [ ] Wearable/paddle sensor integration

---

## Competitive Positioning Summary

### Where We Win RIGHT NOW:
1. **Speed** — 1-2 min vs 30 min – 24 hrs
2. **Cost** — $0.05/video vs $100-400/yr subscription
3. **YouTube analysis** — they can't do this at all
4. **Free CV-only mode** — zero cost, works offline
5. **No video minutes anxiety** — pay per analysis, no subscription

### Where PB Vision Wins (for now):
1. **Depth of stats** — more shot types, quality ratings, 3D viz
2. **Skill ratings** — 6-dimension DUPR-scale system
3. **Mobile app** — native iOS + Android
4. **Social features** — friend tagging, viral growth
5. **Facility partnerships** — B2B distribution
6. **Track record** — established user base and brand

### Our Strategic Angle:
**"The fast, affordable alternative that actually analyzes any pickleball video — including YouTube."**

- PB Vision = premium, slow, subscription-locked
- Us = instant, cheap, open, developer-friendly
- Target the gap: players who won't pay $400/yr but still want analytics
- Target the unique: coaches/analysts who want to study pro YouTube matches
- Target the unserved: drill analytics, rally scoring, APAC market
