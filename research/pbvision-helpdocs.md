# PB Vision — Help Docs Research

> Source: https://help.pb.vision/ (fetched 2026-03-04)
> ~30 help articles reviewed across the full sitemap

---

## 1. What PB Vision Is

PB Vision is an AI-powered pickleball video analysis platform. Users upload game footage, and the system automatically detects rallies, shots, errors, player movement, scoring, and generates performance analytics. It works for **doubles** (primary) and **singles** games. No special hardware required — a smartphone on a tripod is the typical setup.

**Key value prop:** "Turn pickleball video into actionable insights" — shot-by-shot breakdowns, skill ratings, coaching tips, highlights, and data exports.

---

## 2. Technical Approach & How Analysis Works

### Computer Vision Pipeline
1. **Court detection** — AI identifies the four corners of the pickleball court and establishes a coordinate system
2. **Player tracking** — Tracks all 2-4 players throughout the match using visual appearance
3. **Ball tracking** — Detects and tracks the ball frame-by-frame, building shot trajectories
4. **Shot classification** — Classifies each shot by type (serve, return, drop, drive, dink, lob, speedup, smash, reset, poach, passing shot, etc.)
5. **Rally segmentation** — Automatically detects rally boundaries and removes dead time between rallies
6. **Scoring algorithm** — Reconstructs the score sequence based on server identification, serve order, and line calls
7. **Shot quality assessment** — Evaluates each shot's effectiveness using physics-based models

### Ball Speed Calculation
- System identifies a shot and creates a **trajectory** based on ball flight
- Each shot has a **point of impact** and an **end point** (bounce or volley)
- Calculates **average velocity** along the trajectory path (time from point A to point B, divided by distance)
- Speed is NOT peak speed at paddle contact — it's average velocity across the full trajectory

### Shot Quality Model
- **Drops:** Evaluated against an idealized opponent perfectly positioned at the kitchen line. A "sphere" is modeled around the opponent representing their reach. Shots that force the opponent to hit upward = higher quality (green). Does NOT account for opponent's actual position — purely against ideal positioning
- **Drives:** Evaluated on height above net (lower = better) and depth of landing (deeper = better)
- **Lobs:** Evaluated on depth (deeper = better)
- Quality ratings: Excellent 🟢 | Average ⚫️ | Poor 🔴

### Scoring Algorithm
- Assumes **standard rules**: games to 11 or 15, win by 2, non-rally scoring
- Primary input: **server identification and serve order**
- Secondary inputs: line calls (lower confidence — "if it's hard for you to judge an 'out' call, it's challenging for us too")
- Reconstructs a "plausible scoring sequence with minimal corrections"
- Final score is prioritized; running score may be off by a rally or two
- Users can manually correct the final score (not rally-by-rally yet)
- Rally scoring and non-standard formats are NOT currently supported

### AI Chat / "Discuss with AI"
- Two modes: **Copy/Paste** (export data file → attach to any LLM like ChatGPT/Claude/Gemini) and **MCP** (Model Context Protocol — direct integration with Claude Desktop, Gemini Code Assist, Cursor)
- MCP endpoint: `https://share.pb.vision/mcp` (open, no auth needed)
- MCP tools: `get_analysis_guide`, `get_video_insights`, `get_insights_schema`, `get_player_images`, `get_download_url`

### CourtFocus (Mobile App Feature)
- Built-in lock-on indicator in the Android/iPhone app
- Guides users to perfectly center and align the court before recording
- Confirms alignment before allowing recording to start

---

## 3. Stats Tracked

### Player Stats
- **Total shots** — activity level per player
- **Shot accuracy** — in/out/net percentages
- **Serve speed** (median, mph) + percentile vs. all analyzed serves
- **Drive speed** (median, mph) + percentile
- **Court coverage** — heatmap of movement + distance traveled (ft)
- **Serve placement** — court zone breakdown (depth analysis)
- **Return placement** — court zone breakdown
- **Out fault percentage** — % shots hit out
- **Net fault percentage** — % shots hit into net
- **Shot counts** by type: volleys, ground strokes, backhands, forehands
- **Average shot quality** per type
- **Ball directions** — placement pattern analysis (left/cross/right counts)

### Shot Type Breakdowns
Each shot type group includes:
- `average_baseline_distance`
- `average_height_above_net`
- `average_quality`
- `count`
- `median_baseline_distance`
- `median_height_above_net`
- `speed_stats`
- `outcome_stats` (success_percentage, rally_won_percentage)

Shot groups tracked: backhands, dinks, drives, drops, fifths, forehands, fourths, kitchen_area, left_side_player, lobs, mid_court_area, near_baseline_area, near_left_sideline_area, near_midline_area, near_right_sideline_area, passing, poaches, resets, returns, right_side_player, serves, smashes, speedups, third_drives, third_drops, third_lobs, thirds

### Team Stats
- **Percentage to kitchen** — % of rallies where both players reached the kitchen
- **Shot distribution** — split between partners
- **Left side play** — stacking indicator (50/50 = no stacking, 90/10 = heavy stacking)
- **Team thirds/fourths/fifths percentage** — who's taking key shots
- **Short/medium/long rally wins** — where the team excels

### Game Stats
- Total rallies
- Kitchen rallies (all players at net)
- Average shots per rally
- Longest rally

### Highlights Detection
Automatically identifies: ATPs (around-the-post), Ernes, Poaches, Firefights, Long Rallies

### Skill Ratings (2.0–8.0 scale, currently caps at 5.5)
Six dimensions:
1. **Serve** — speed, depth, placement variety, fault rate, return difficulty forced
2. **Return** — depth, speed, hang time, fault rate, quality of opponent's resulting 3rd shot
3. **Offense** — attack frequency, speedup success, placement, points won from attacks
4. **Defense** — reset quality, recovery speed, kitchen positioning after being pushed back
5. **Agility** — movement speed, kitchen arrival time, stability during shots, positioning efficiency
6. **Consistency** — fault rate, unforced errors, variability in rally outcomes

**Lifetime rating** = weighted average of 90 most recent games (recent games weighted higher)

**Rating vs DUPR:** PB Vision measures *performance* (how you played); DUPR measures *results* (who won). Same 2.0-8.0 scale but different things. Currently doubles only, singles planned.

### 3D Shot Chart
Interactive visualization of shot trajectories for serves (1st), returns (2nd), 3rd/4th/5th shots — filterable by drops, drives, lobs

---

## 4. Data Export & API

### Export Formats
Three data layers available for download:
1. **Stats** — Advanced statistics in JSON/Excel. Schema: https://pbv-public.github.io/stats
2. **Insights** — App-level data powering the UI. Schema: https://pbv-public.github.io/insights
3. **CV (Computer Vision)** — Low-level raw CV data. Schema: https://pb-vision.github.io/schemas-cv

Also supports:
- **EDL timeline export** — for use in DaVinci Resolve, Premiere, etc. to create highlight reels
- **Rally-only video** — dead time automatically removed, exportable

### Partner API
- REST API for approved partners (camera companies, facilities, tournament operators, app developers)
- Webhook-based: submit video → receive JSON callback with shot-level insights, rally structure, stats, player movement
- Requires Annual Premium subscription + API Add-on
- SDK: https://github.com/pbv-public/partner-sdk-nodejs
- Pricing: $8/hr video (HD), $12/hr (4K) — ~$1.60-$2.40 per 12-min game

---

## 5. Video Requirements & Camera Setup

### Supported Video Specs
| Spec | Requirement |
|------|-------------|
| Frame Rate | 30 or 60 FPS |
| Video Codec | H.264 |
| Resolution | 1080p or 4K |
| File Extension | .mp4 |
| Audio Encoding | MPEG-4 AAC |
| Max Bitrate | 4 Mbps |
| Max File Size | 5 GB |
| Max Length | 30 minutes |
| Orientation | **Landscape only** |
| Aspect Ratio | 16:9 preferred; others work if court is visible |

### Recording Requirements
- **All 4 corners of the court** must be visible — no parts cut off
- **All players fully visible** at all times (including when serving)
- **Camera must be stable** — no handheld, no movement during filming
- **Camera height:** minimum 5 feet off the ground
- **Lighting:** avoid direct sunlight behind camera; shade/shadows cause issues
- **One complete game** per video (first serve → paddle tap)
- **No warm-ups, drills, or incomplete games**
- **Do NOT trim dead time between rallies** — PB Vision uses it for calibration
- **Disable image stabilization and HDR** on phones (if recording outside PB Vision app)
- **Single camera angle only** — no multi-angle cuts (tournament broadcasts often fail for this reason)
- Recommended: **1080p at 30fps** for best balance of quality and file size; 4K works but gets compressed locally

### Camera Options
- **Any device works:** smartphone, GoPro, DSLR, any digital camera at 30fps+
- **Phone on tripod** is the most common setup (0.5x wide angle often needed)
- **Fenced courts:** spring clamp mount on fence (~30 sec setup)
- **Open courts:** standard tripod with ball head, legs extended to 5ft+
- **Best angles:** center or corner, wide-angle, at least 5 feet high
- **PB Vision mobile app** has built-in recording with CourtFocus alignment guide

### Processing
- Most videos processed in **~30 minutes** depending on server load
- "Taking Longer Than Expected" = flagged for manual engineering review (usually resolves within 24 hours)
- **Do not re-upload** failed videos — re-uploads consume additional minutes

---

## 6. Accuracy & Limitations

### Accuracy
- **95%+ accuracy** on shot detection and scoring when framing guidelines are followed
- Self-reported; based on proper recording conditions

### Known Limitations & Failure Modes
1. **Poor framing** — court corners cut off → processing issues or inaccurate data
2. **Shade/poor lighting** — partial shade across court is "especially challenging"
3. **Camera movement** — even small shifts throw off court alignment
4. **Low ball-to-court contrast** — yellow ball on yellow/tan court = hard to track
5. **Players leaving frame** — even briefly causes AI to lose track
6. **Similar player appearance** — players in same color may get swapped
7. **Players overlapping** — common at kitchen line, causes identity confusion
8. **Edge-case serves** — very fast or body-obscured serves may be missed
9. **Shadow/netting obstruction** — ball obscured by shadows or net
10. **Close line calls** — "just like human referees, these are genuinely difficult"
11. **Lighting transitions** — sun moving behind clouds mid-game
12. **Drills not supported** — only traditional singles/doubles gameplay
13. **Rally scoring not supported** — only standard (side-out) scoring to 11 or 15
14. **Score corrections** — only final score can be manually corrected, not rally-by-rally
15. **Skill rating cap at 5.5** — upper limit of current model confidence
16. **Shot quality doesn't account for actual opponent position** — uses idealized positioning
17. **Multi-camera videos fail** — tournament broadcasts with angle changes won't work
18. **SwingVision exports may fail** — if dead time between rallies is removed, PB Vision misinterprets entire video as one continuous rally
19. **Unsupported codecs** — H.265/HEVC, VP9, AV1, DaVinci Resolve defaults may fail
20. **Portrait orientation** — may not process correctly
21. **Net Impact Score** — "work in progress, for now you will just see 50%"

### Automatic Failure Detection & Refunds
AI auto-detects and refunds minutes for:
- Significant camera motion
- Court boundaries not visible
- Video is not of a pickleball match
- Users get a 5% bonus pool of automatic refund minutes

---

## 7. Facility & Club Integration ("Court Insight")

Three integration paths:
1. **Phone recording** — tripod/wall/fence mounts, players upload via app. Zero cost to club.
2. **PodPlay integration** — full in-venue system with digital scoreboards, court management, revenue sharing. Infrastructure-level costs.
3. **Save My Play integration** — QR-code-activated cameras ($185/camera + $49/court/month), PB Vision analytics at ~$1.60/game base.

All options support ratings, leagues, clinics, coaching, player engagement.

---

## 8. Pricing Model

### Subscriptions
- **Free tier:** 1 video upload (up to 25 min)
- **Starter Pass:** $19.99/mo (100 min/mo) or $99.99/yr (1,200 min/yr)
- **Premium Pass:** $49.99/mo (400 min/mo) or $396/yr (4,800 min/yr)
  - Adds: unlimited storage, 4K+60fps, API access, beta features

### Minute Packs (add-on)
- 60 min: $9.99 (~$2/game)
- 300 min: $39.99 (~$1.60/game)
- 1,200 min: $99.99 (~$1/game)

Minutes don't expire; roll over while subscription active. Minimum charge: 5 minutes per video.

---

## 9. Key Takeaways for Our Project

### What PB Vision Does Well
- Comprehensive shot-by-shot analysis from a single camera angle
- Rich stat taxonomy (dozens of metrics per player per game)
- 3D shot visualization
- Skill rating system across 6 dimensions
- Data export at multiple levels (stats, insights, raw CV)
- Open MCP endpoint for AI analysis integration
- Partner API for programmatic access

### Where There's Room to Compete/Differentiate
- **Accuracy limitations** are significant — 95% under ideal conditions, degrades fast with suboptimal video
- **No drill support** — only full games
- **No rally scoring** support
- **Skill ratings cap at 5.5** — can't distinguish high-level players
- **No real-time analysis** — upload and wait ~30 min
- **Single camera angle only** — no multi-camera fusion
- **Shot quality model is simplistic** — doesn't account for actual opponent position/movement
- **Net Impact Score** is essentially a placeholder (always 50%)
- **Minutes-based pricing** creates friction for heavy users
- **Player identity confusion** is a known persistent issue
- **No biomechanical analysis** (paddle angle, body mechanics, etc.)
- **Speed is average velocity, not peak** — less useful for training power
