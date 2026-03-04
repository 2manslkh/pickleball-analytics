# Frontend Development

## Stack
- **Framework:** Next.js 15 (App Router)
- **Styling:** Tailwind CSS v4 (PostCSS plugin)
- **Language:** TypeScript
- **Location:** `frontend/`

## Design System
Dark theme with CSS variables defined in `app/globals.css`:

| Variable | Value | Usage |
|----------|-------|-------|
| `--bg` | `#0a0a0a` | Page background |
| `--bg-card` | `#141414` | Card/panel background |
| `--bg-card-hover` | `#1a1a1a` | Card hover state |
| `--border` | `#262626` | Borders |
| `--text` | `#fafafa` | Primary text |
| `--text-secondary` | `#a3a3a3` | Secondary text |
| `--accent` | `#22c55e` | Green accent (primary actions) |
| `--accent-dim` | `#16a34a` | Green accent hover |
| `--warning` | `#f59e0b` | Yellow/warning |
| `--danger` | `#ef4444` | Red/error |
| `--blue` | `#3b82f6` | Blue accent |
| `--purple` | `#a855f7` | Purple accent |

## Shot Type Colors (consistent across all components)
```typescript
const shotColors: Record<string, string> = {
  serve: "#3b82f6",    // blue
  return: "#8b5cf6",   // purple
  dink: "#22c55e",     // green
  drive: "#ef4444",    // red
  drop: "#f59e0b",     // yellow
  lob: "#06b6d4",      // cyan
  volley: "#ec4899",   // pink
  overhead: "#f97316", // orange
};
```

## Team Colors
- Team 0 (Near): `#22c55e` (green)
- Team 1 (Far): `#3b82f6` (blue)

## Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `VideoPlayer` | `components/VideoPlayer.tsx` | Video + timeline + markers + controls |
| `StatsPanel` | `components/StatsPanel.tsx` | Full stats sidebar |
| `UploadZone` | `components/UploadZone.tsx` | YouTube URL input + file drop + mode toggle |

## Types
All TypeScript interfaces in `lib/types.ts` — mirrors the Python Pydantic models.

## API Client
`lib/api.ts` — `analyzeYouTube()` and `analyzeUpload()` functions.
Uses `NEXT_PUBLIC_API_URL` env var for Modal URL (empty = dev proxy).

## Proxy (dev mode)
`next.config.ts` rewrites `/api/*` to `http://localhost:8000/*` for local FastAPI dev.

## Key Patterns
- All components are `"use client"` (client-side rendering)
- Use CSS variables for all colors: `bg-[var(--bg-card)]`
- Tabular numbers for stats: `className="tabular-nums"`
- Cards: `bg-[var(--bg-card)] border border-[var(--border)] rounded-xl p-4`
- Responsive grid: `grid grid-cols-1 lg:grid-cols-3 gap-6`

## Adding New Stats/Visualizations
1. Add type to `lib/types.ts`
2. Add component in `components/`
3. Import in `StatsPanel.tsx` or create new panel
4. Add to page layout in `app/page.tsx`
