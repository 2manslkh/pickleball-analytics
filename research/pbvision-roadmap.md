# PB Vision Roadmap Analysis

> Source: https://pbvision.featurebase.app/roadmap
> Scraped: 2026-03-04
> PB Vision is a pickleball analytics platform powered by AI — users record games, upload video, and get AI-generated stats, ratings, shot analysis, coaching tips, and more.

---

## Current Product (Shipped Features)

Based on help center and completed roadmap items, PB Vision currently offers:

### Core Features
- **AI Video Processing** — Upload pickleball game videos for automated analysis
- **Rally Detection** — Automatic identification of rallies and dead time
- **Shot Detection & Classification** — Identifies shot types (drives, drops, lobs, dinks, etc.)
- **Shot Explorer** — Filter and browse individual shots across games
- **Scoreboard Overlay** — AI-generated score tracking on video playback
- **Video Player** — In-app playback with shortcuts
- **Video Library** — Organize games into folders
- **Court Coverage Heat Maps** — Visualize player positioning
- **Kitchen Arrival Stats** — Track how quickly players get to the kitchen line

### Analytics & Ratings
- **Vision-Based Skill Ratings (2.0–8.0 DUPR scale)** — AI rates each player across 6 skill categories:
  - Serve, Return, Offense, Defense, Agility, Consistency
- **Cross-Game Trends** — Track stats improvement over time (the "Me" page)
- **Unforced Error Tracking** — Differentiates forced vs unforced errors with location data
- **Leaderboards** — Summarize player impact and performance per game
- **Identify Shots That Would Have Gone Out** — Flags volleys on balls heading out of bounds
- **3rd Shot Analysis** — FH/BH drop %, drive %, and effectiveness charts

### AI & Coaching
- **AI Coaching Tips** — Personalized coaching insights per game with trend recognition
- **"Discuss with AI Chat"** — Export game data (insights.json) for LLM-based analysis
- **Data Exports** — Advanced stats export for deeper analysis

### Platform
- **Singles Support** — Analysis works for singles games
- **Scoreboard Overlays** — Score tracking on video
- **Better Pricing & Monthly Option** — Flexible subscription plans
- **Live Court Validation (iOS)** — Real-time camera alignment check during recording
- **Sharing** — Share videos and public player profiles
- **Court Insight for Facilities** — Enterprise/facility-level analytics
- **API Partner Guide** — Integration capabilities
- **Ambassador Program** — Referral/community program

### Pricing (current)
- Plans range ~$99–$400/year (based on user feedback references)
- Minutes-based processing model

---

## Roadmap: In Progress (5 items)

| Feature | Votes | Comments | ETA | Priority | Description |
|---------|-------|----------|-----|----------|-------------|
| **Shot and Highlight Editing** | 68 | 21 | — | — | Edit AI-detected shots/highlights: delete rallies/shots/highlights, reclassify shot type/attribute/quality. V1 scope defined. |
| **Reel Creator** | 43 | 7 | 2026-03-02 | High | Create reels from starred shots/highlights across videos. Crop for social media (TikTok vertical). Export or download mp4. Auto-reels from AI highlights (ATPs, Ernes, poaches, firefights). |
| **Just the Rallies Exporter** | 34 | 5 | 2026-03-02 | High | Export gameplay-only video with dead time trimmed. Previously existed, being brought back. Great for coaches and social sharing. |
| **Automatic Game Splitting** | 24 | 5 | — | — | Upload 1–2 hour continuous video → auto-split into individual games. Eliminates need to start/stop recording. Helps with multi-court/tripod setups. |
| **Video Player V2** | 17 | 7 | 2026-03-02 | High | Mobile-first redesign. Telestrate (draw on video) mode. Video export capability. Optimized for pickleball review workflows. |

---

## Roadmap: Planned (4 items)

| Feature | Votes | Comments | Description |
|---------|-------|----------|-------------|
| **Drill Session Recordings** | 97 | 20 | Support non-game recordings (ball machine, partner drills, serving practice). Analyze specific shot types in practice context. Highest-voted feature request overall. |
| **On Device Processing** | 21 | 2 | Full local processing on phone (Part 1 — Live Court Validation — is done). Would enable lower-cost plans by avoiding cloud compute. |
| **Left-Handed Player Support** | 15 | 4 | Profile setting for handedness. Fix forehand/backhand labeling for lefties. Currently all players assumed right-handed. |
| **Streamline Multi-Game LLM Export** | 3 | 1 | Bulk-select games from library → single export for AI Chat. Zip insights.json files together. Better UX for multi-game analysis. |

---

## Community Requests: In Review (19 items)

These are user-submitted feature requests not yet on the official roadmap.

### High Interest (4+ votes)
| Feature | Votes | Description |
|---------|-------|-------------|
| **Upload Score with Game** | 4 | Enter final score on upload to constrain AI processing — should produce more accurate data. Don't charge for obviously wrong results. |
| **Aggregate Stats Across Games** | 4 | See total combined stats for a player across multiple games/folders, not just per-game. |
| **Manual Scoreboard Override** | 4 | Point-by-point manual score correction when AI gets it wrong. High value for sharing and social media posting. |
| **Rally Scoring Support** | 4 | Support rally scoring (common in Singapore, Malaysia). Currently only sideout scoring. International expansion blocker. |

### Medium Interest (2-3 votes)
| Feature | Votes | Description |
|---------|-------|-------------|
| **iPad App** | 3 | Fully compatible iPad version for larger screen analytics viewing. |
| **Filter/Sort Library by Ratings** | 2 | See DUPR/performance ratings in video library list view. Sort/filter by rating to find best/worst games. |
| **Court Coverage Heat Map Improvements** | 2 | Add recommendations, arm-span adjustment, filter by serving/receiving side. Currently hard to extract insights from. |

### Newer Requests (1 vote)
| Feature | Votes | Description |
|---------|-------|-------------|
| **Friends Tab** | 1 | Find tagged friends, track friend records, compare head-to-head stats, cross-reference games played with/against. |
| **Male/Female Player Support** | 1 | Separate ratings by sex. Female players rated lower in mixed doubles due to slower shot speeds vs all-male benchmarks. |
| **Plus/Minus Metric** | 1 | +/- score like traditional sports — did you cause the point win/loss, or was it a great/poor shot by someone else? |
| **Highlight & Lowlight Reels** | 1 | Auto-generate per-player best shots reel and "needs work" reel. (Overlaps with Reel Creator in progress.) |
| **Kitchen Arrival Chart UX** | 1 | Aggregate kitchen arrival stats to daily average line graph (like ratings), not individual game points. |
| **Kitchen Arrival Stat Inconsistency** | 1 | ME page number doesn't match Leaderboard and Game Stats numbers — bug/consistency issue. |
| **Add Player Profile to AI Prompt** | 1 | Feed handedness, stacking preference to AI Chat for more relevant analysis. |
| **Offline Processing** | 1 | Provide container/local GPU processing option. Different from on-device — use own hardware. Address cloud capacity delays. |
| **Shot Analysis Summary Report** | 1 | Summary per shot type on ME tab — track shot-level improvement over time. |
| **Singles Rating Parity** | 1 | Automated rating feature for singles games (currently limited compared to doubles). |
| **Ratings by Game Count** | 1 | Show ratings based on rolling 5-game windows instead of calendar date to reduce noise. |
| **Trending Badges** | 1 | Show up/down trend indicators for each of the 6 skill facets on player summary. |

---

## Gaps & Opportunities Analysis

### 🔴 Critical Gaps

1. **Drill/Practice Mode (97 votes — #1 request)**
   - Players spend significant time practicing, not just playing games. No analytics for practice sessions is a major gap.
   - *Opportunity: Practice analytics could be a premium upsell or coaching-focused tier.*

2. **Social/Community Features**
   - No friends system, no head-to-head comparisons, no social sharing of stats
   - The "Friends Tab" request hints at strong desire for social pickleball analytics
   - *Opportunity: Social graph + competitive comparisons could drive viral growth and retention.*

3. **Scoring Accuracy & User Correction**
   - Multiple requests around score inaccuracy — manual override, upload score constraints
   - Scoring errors undermine trust in all downstream analytics
   - *Opportunity: User-in-the-loop correction → better training data → improved AI accuracy. Feedback flywheel.*

### 🟡 Notable Gaps

4. **International & Inclusivity**
   - Rally scoring (Singapore, Malaysia) not supported — blocks Asia-Pacific expansion
   - Left-handed players get inaccurate data — ~10% of players
   - Male/female rating normalization missing — affects mixed doubles
   - *Opportunity: Southeast Asia is a fast-growing pickleball market. Rally scoring support = market entry.*

5. **Platform Breadth**
   - No iPad app (only mobile phone)
   - No web app mentioned for desktop viewing
   - No offline/local processing option
   - *Opportunity: iPad + web would unlock coaching sessions, facility use, tournament review.*

6. **Advanced Analytics**
   - No +/- impact metric (common in other sports)
   - No per-shot-type trend tracking over time
   - No partner synergy analysis (how do specific partnerships perform?)
   - No opponent scouting reports
   - *Opportunity: "Moneyball for pickleball" — advanced metrics for competitive players and coaches.*

7. **Content Creation Pipeline**
   - Reel Creator is in progress but not shipped yet
   - No automatic social media sharing integrations
   - No tournament/event compilation features
   - *Opportunity: Becoming the content creation engine for pickleball social media could drive organic marketing.*

### 🟢 Opportunities Not on Their Radar

8. **Team/Club Management**
   - No club dashboards, team rosters, league management
   - Court Insight exists for facilities but seems basic
   - *Opportunity: B2B play — clubs, leagues, tournament organizers as paying customers.*

9. **Live/Real-Time Analytics**
   - Everything is post-game analysis. No real-time scoring or live stats.
   - *Opportunity: Live streaming + real-time stats overlay for tournaments.*

10. **Coaching Marketplace**
    - AI coaching tips exist, but no connection to human coaches
    - *Opportunity: Let coaches review student videos with annotations, create lesson plans from data.*

11. **Wearable/Sensor Integration**
    - Pure vision-based — no integration with paddles, smartwatches, heart rate
    - *Opportunity: Combine video analytics with paddle sensor data (spin, force) for richer insights.*

12. **Gamification & Challenges**
    - No challenges, achievements, skill milestones
    - *Opportunity: "Hit 100 third-shot drops this month" — drives engagement and recording frequency.*

13. **API/Data Platform**
    - API exists but seems partner-focused, not open
    - No public API for community developers
    - *Opportunity: Platform play — let others build on PB Vision data.*

---

## Competitive Positioning Notes

- PB Vision is the clear **market leader** in AI-powered pickleball video analytics
- Pricing ($99–$400/yr) and cloud processing costs are user concerns
- The minutes-based model creates anxiety about "wasted" processing on bad results
- Community is engaged (active FeatureBase board) and technically sophisticated
- ETA dates are recent (March 2026) suggesting active development velocity
- The team (PB Vision Team posts) is responsive and creates roadmap items from feedback

### Key Takeaways for a Competitor

1. **Drill analytics** is the single biggest unmet need (97 votes, 20 comments)
2. **Data accuracy** (scoring, shot classification) is a trust issue — getting it right matters more than new features
3. **Social features** are essentially non-existent — huge white space
4. **International markets** (Asia-Pacific) are underserved due to rally scoring gap
5. **Content creation** (reels, exports) is highly desired — pickleball + social media is a natural fit
6. **Pricing sensitivity** exists — a freemium or lower-cost tier with on-device processing could disrupt
