# PB Vision — Competitor Analysis

**Company:** Pickleball Vision AI Inc.  
**Website:** https://pb.vision/  
**Tagline:** "Pickleball analytics powered by AI"  
**Tech Stack:** React SPA (Vite), Firebase Auth, Google Cloud Storage, Mux video, Algolia search, Zendesk support  
**Platforms:** iOS (Apple App Store), Android (Google Play Store), Web app  
**Last researched:** 2026-03-04  

---

## Product Overview

PB Vision is an AI-powered pickleball analytics platform that processes uploaded game video to deliver detailed shot-by-shot breakdowns, player performance metrics, and personalized coaching insights. Users record their games (via phone, tablet, or facility-installed cameras), upload the video, and the AI engine analyzes every shot, rally, and player movement.

**Core value proposition:** "Experience the future of pickleball with PB Vision analytics" — turn raw game footage into actionable data to improve your play. Positioned as the data-driven coaching assistant for all skill levels.

**Key testimonial quote (from their site):**  
> "PB Vision is the real deal. They're the first I've seen to seamlessly connect AI & pickleball — giving players the data they actually need to actually get better."

---

## Key Features

### 1. AI Video Analysis
- Upload game video → AI processes it (typically within 3 hours, up to 24 hours)
- Automatic player tracking, shot detection, and rally segmentation
- Shot classification: drives, drops, dinks, lobs, smashes, resets, volleys, Erne, ATP (Around The Post)
- Shot quality assessment (green = high quality, red = low quality)
- Error tracking: faults (net, out), unforced errors, popup tracking

### 2. Shot Explorer
- Filter and search through all shots in a video
- Filter by: shot type (drive, drop, lob, smash, dink, Erne, ATP), quality, errors, player
- Preset filters: e.g., "My 3rd Shot Drops" — can add error filters (e.g., only net errors)
- **Global presets** — apply across all videos (e.g., "My 3rd Shot Drops" on any game)
- **Video-specific presets** — saved to a specific video, shared with anyone who views it
- Shot window controls: view N shots before/after a selected shot

### 3. Pattern Explorer
- Analyze shot patterns and sequences across games
- Filter by rally types and shot sequences

### 4. Game Analytics / Statistics
- **Macro trends:** In/out/net percentages, kitchen arrival percentage on serve, serve depth, return depth, court coverage
- **Micro analysis:** 3D trajectory for individual shots, speed, bounce location
- Team stats and player comparison within a game
- Average speed tracking per shot type

### 5. AI Coach Corner
- Personalized coaching tips generated per game
- Click on your player image → AI generates advice based on your actual gameplay
- Key coaching areas:
  - Serves, returns, dinks, drops, resets, and other key shots
  - Kitchen control and shot selection strategy
  - Strengths and improvement areas with helpful graphics
  - Specific, practical, data-backed advice

### 6. Skill Rating System
- AI-generated skill rating (their version of DUPR)
- Rates individual skills: serves, returns, overall play
- Per-game and aggregate ratings
- **User feedback:** Ratings sometimes inflated by 0.25–0.5 points vs. DUPR; serve/return ratings can be inaccurate (per Reddit reviews)

### 7. Highlights
- Auto-generated game highlights
- "Watch highlight on repeat" feature
- Shareable highlight clips

### 8. Friend Tagging
- Tag other players in your uploaded video
- Tagged friends receive the same game analysis **for free**
- Referral system: refer friends → earn bonus video minutes

### 9. Recording Tools
- **Mobile app:** One-tap recording directly from the app
- **Facility cameras:** Fixed court-side camera system with tablet control
- **QR code start:** Players scan QR to begin recording at a facility

### 10. AI-Powered LLM Integration
- Appears to have an LLM endpoint for generating game summaries in markdown
- Can attach multiple game files and analyze together with a single prompt
- URL pattern: `api-2o2klzx4pa-uc.a.run.app/video/llm.md` (Google Cloud Run)

### 11. Progress Tracking (Upcoming/Voted Feature)
- "Create a history of student stats and insights to measure improvement over time" — listed as a feature users can upvote

---

## Pricing

### Consumer Plans (Subscription-Based "Video Minutes")

PB Vision uses a **video minutes** model — 1 video minute = 1 minute of game footage processed. A typical 15-minute game uses 15 video minutes.

| Plan | Annual Price | Monthly Equivalent | Monthly Price (no annual) | Video Minutes |
|------|-------------|-------------------|--------------------------|---------------|
| **Free** | $0 | $0 | $0 | 1 free game upload (anonymous users get 1 video) |
| **Starter** | $99.99/year | $8.33/mo | $19.99/mo | 300 video minutes/year |
| **Premium** | ~$396–399/year | ~$33/mo | $49.99/mo | 1,200 video minutes/year (~100 games) |

**Additional details:**
- "Save up to 88% with 1 year premium access"
- Bonus video minutes for annual subscribers
- Can purchase additional video minutes à la carte ("Buy More Video Minutes")
- **Referral program:** "Get Free Video Minutes When You Refer a Friend" — both referrer and friend receive bonus minutes

### Starter Plan Includes:
- Basic game analysis
- Learning tools and stats (kitchen arrival, shot quality assessment)

### Premium Plan Includes ($200/year value per giveaway post):
- 60 game analysis credits (from giveaway — may differ from standard)
- Friend tagging (others get free analytics)
- Full analytics: macro trends (in/out/net %, kitchen arrival, serve depth)
- Micro analysis (3D trajectory, speed, bounce location)
- Shot Explorer and Pattern Explorer access
- Facility usage at participating partners
- Coach Corner (personalized AI coaching)
- Leaderboards

### Facility / B2B Model ("Save My Play")

**Hardware:**
- $185 per camera (one-time setup fee)
- $49 per month per court
- Volume discounts available for multi-court clubs
- Court-side tablet: $99 per tablet for one-tap recording control

**Player pricing at facilities:**
- **No cost for the facility** — players pay directly
- Players purchase analytics via QR code checkout ("Save My Play")
- **$8 per hour of video** (e.g., a 12-minute game costs $1.60)
- Friends tagged in facility recordings get analytics for free

**API/Enterprise Licensing:**
- Fees based on video-minutes or videos processed per month
- Cost per video-minute determined through individual agreements
- Monthly invoicing based on actual usage

---

## Target Audience

### Primary Segments:
1. **Recreational players (3.0–4.5 DUPR)** — want to identify weaknesses and improve
2. **Competitive/tournament players** — data-driven performance optimization
3. **Coaches** — "Built by Pickleball Players for Coaches Like You"
   - Record student gameplay and upload for analysis
   - Track student progress over time
   - Data-backed coaching conversations
4. **Facilities/Clubs** — camera installation for member engagement and revenue

### Geographic:
- Primarily US market (pickleball's largest market)
- Eligible worldwide ("100% digital, winners from anywhere")

---

## UX & User Experience

### Strengths (from user reviews/content):
- Impressive AI analysis depth — shot classification, 3D trajectory, quality scoring
- Clean web interface with video player integration
- Shot Explorer is a standout feature — filter and replay specific shot types
- Friend tagging is a strong social/viral feature
- Free first game lowers barrier to try
- Multi-platform (iOS, Android, Web)
- Active Discord community
- Responsive product team

### Pain Points (from Reddit reviews):
- **Processing time:** 3–24 hours wait for analysis results
- **Shot attribution errors:** Some shots credited to wrong player
- **Rating accuracy:** Skill ratings can be off by 0.25–0.5 DUPR points; serve/return ratings sometimes wildly inaccurate
- **Upload experience:** Delays, errors, inconsistent processing times
- **Video minutes feel limited:** 100 games/year on Premium may not be enough for frequent players (30+ games/week)
- **Black Friday issues:** Poor first-time experience reported
- **Behavioral impact:** Some users found themselves "overplaying for the video/app" rather than playing naturally

### Key UX Quote (Reddit):
> "I tried PB vision for a game video and although it is not completely accurate but still impressed with it."

---

## Competitive Positioning

### PB Vision vs. SwingVision
- SwingVision is the primary competitor (frequently compared on Reddit)
- SwingVision offers real-time scoring and an "AI coach" at max tier
- PB Vision differentiates on **depth of analytics** and **actionable insights**
- User quote: "I switched to PB Vision from SwingVision, and it's been a game-changer. While SwingVision was fine for recording games, PB Vision delivers actionable insights that have boosted my performance, taking me from a DUPR 4.0 to 4.5."

### Key Differentiators:
1. **Post-game cloud processing** (not real-time) — enables deeper analysis
2. **3D shot trajectory visualization**
3. **Shot Explorer with complex filtering** (shot type + quality + error + sequence)
4. **Pattern Explorer** for strategic analysis
5. **AI Coach Corner** with personalized per-game tips
6. **Friend tagging** — social/viral growth mechanism
7. **Facility partner program** — B2B revenue model
8. **Video minutes model** rather than game-count model
9. **Web app** in addition to mobile (SwingVision is Apple-only)

---

## Business Model Summary

| Revenue Stream | Model | Pricing |
|---------------|-------|---------|
| Consumer subscriptions | SaaS (video minutes) | $99–$399/year or $19.99–$49.99/month |
| Pay-per-play (facilities) | Transaction fee | $8/hour of video |
| Facility hardware | Hardware + SaaS | $185 setup + $49/mo/court |
| Tablet add-on | Hardware | $99/tablet |
| API licensing | Usage-based B2B | Custom pricing per video-minute |
| Additional video minutes | À la carte | Unknown pricing |

---

## Technology & Infrastructure

- **Frontend:** React (Vite build), Material UI (MUI), HLS.js for video streaming
- **Backend:** Google Cloud (Firebase Auth, Cloud Functions/Run, GCS for storage)
- **Video:** Mux for video hosting/streaming, HLS delivery
- **AI/ML:** Custom computer vision models for shot detection, trajectory analysis, player tracking
- **Search:** Algolia for in-app search
- **Analytics:** Mux Data, custom analytics pipeline
- **Support:** Zendesk, Discord community
- **Payments:** In-app purchases (iOS/Android) + web payments
- **Domain:** pb.vision (short, memorable)
- **Cloud storage:** `storage.googleapis.com/pbv-pro-dev/` and `storage.googleapis.com/pbv-pro/`
- **API:** `api-2o2klzx4pa-uc.a.run.app` (Google Cloud Run)
- **Help center:** help.pb.vision

---

## Strengths & Weaknesses

### Strengths:
- Deep, comprehensive analytics (3D trajectory, shot quality, pattern analysis)
- Multi-platform availability (iOS, Android, Web)
- Strong B2B facility model creates distribution channel
- Friend tagging drives organic/viral growth
- Free trial (1 game) lowers acquisition barrier
- Active community (Discord) and responsive team
- Coach-focused features and positioning
- Referral program for growth

### Weaknesses:
- Cloud processing delay (3–24 hours) — not real-time
- Accuracy issues with shot attribution and skill ratings
- Video minutes model can feel restrictive for heavy users
- Premium pricing ($399/year) is significant for recreational players
- No real-time scoring/line calling (vs. SwingVision)
- SPA architecture means poor SEO (all content behind JS)
- Processing infrastructure appears to have reliability issues

---

## Opportunities for a Competitor:

1. **Real-time or near-real-time analysis** — biggest gap vs. PB Vision
2. **More accurate shot attribution** — known pain point
3. **Better rating calibration** — align more closely with DUPR
4. **Unlimited analysis** for subscribers — remove video minutes friction
5. **Lower price point** — $99–$199/year for full features could undercut
6. **Better onboarding/first-time experience** — PB Vision's is reportedly rough
7. **Real-time scoring** during games — PB Vision doesn't offer this
8. **Social features** beyond friend tagging — leaderboards, challenges, community
9. **Coach marketplace** — connect players with coaches based on analytics
10. **Integration with DUPR** or other official rating systems
