# Hacker Crush - Game Design Document

**Date:** 2026-01-14
**Status:** Approved

## Overview

A Candy Crush clone with a cybersecurity/hacker theme, built in Python using Pygame and deployable to Vercel via Pygbag (WebAssembly).

## Tech Stack

- **Game Engine:** Pygame 2.x (Python)
- **Web Deployment:** Pygbag (compiles Pygame to WebAssembly)
- **Hosting:** Vercel (static files + serverless)
- **Database:** Vercel KV (Redis)
- **API:** Vercel Serverless Functions (Python)

## Project Structure

```
hacker-crush/
├── src/
│   ├── main.py           # Entry point, game loop
│   ├── board.py          # Grid logic, matching
│   ├── candy.py          # Candy classes & specials
│   ├── animations.py     # Swap, fall, explode animations
│   ├── audio.py          # Sound & music manager
│   ├── ui.py             # Menus, HUD, leaderboard
│   └── api_client.py     # Leaderboard HTTP calls
├── assets/
│   ├── images/           # Candy sprites, backgrounds
│   ├── sounds/           # SFX files
│   └── music/            # Background track
├── api/
│   └── scores.py         # Vercel serverless function
├── tests/                # TDD test suite
│   ├── test_board.py
│   ├── test_candy.py
│   ├── test_matching.py
│   └── test_api.py
├── build/                # Pygbag output (generated)
├── vercel.json           # Vercel config
└── requirements.txt
```

## Game Mechanics

### Grid System

- 8x8 board = 64 cells
- 6 candy types: Black Hat, DEF CON, Security Ronin, Lock, Key, Virus
- Random fill ensuring no initial matches

### Matching Rules

- 3+ in a row/column = match
- Matches clear and score points
- Gravity fills gaps from above
- New candies spawn at top

### Special Candies

| Formation | Creates | Effect |
|-----------|---------|--------|
| 4 in a row | **Striped** | Clears entire row OR column (based on swipe direction) |
| L or T shape | **Wrapped** | Explodes 3x3 area, then explodes again |
| 5 in a row | **Color Bomb** | Clears ALL candies of the color it's swapped with |

### Special Combinations

| Combo | Effect |
|-------|--------|
| Striped + Striped | Clears row AND column |
| Striped + Wrapped | Clears 3 rows AND 3 columns |
| Wrapped + Wrapped | 5x5 explosion |
| Color Bomb + Striped | All of that color become striped, then activate |
| Color Bomb + Wrapped | All of that color become wrapped, then activate |
| Color Bomb + Color Bomb | Clears entire board |

### Scoring

- Base: 10 points per candy
- Cascade multiplier: x1.5 per chain level
- Special activation bonuses: +50 (striped), +100 (wrapped), +500 (color bomb)

## Game Modes

### 1. Endless Mode (Zen Hack)

- No time/move limit
- Play until no valid moves remain
- Board reshuffles if stuck (3 reshuffles max, then game over)
- Goal: Maximize score

### 2. Moves Mode (Precision Strike)

- 30 moves to reach target score
- Target increases each level: 5,000 -> 10,000 -> 20,000...
- Stars awarded: 1 (target), 2 (x1.5), 3 (x2)
- Unused moves = bonus points (100 per move)

### 3. Time Attack (Speed Run)

- 90 seconds on the clock
- +3 seconds per special candy created
- +5 seconds per combo (4+ chain)
- Frantic pace, encourages risky plays

### Difficulty Progression (Moves Mode only)

- Level 1-5: Standard gameplay
- Level 6-10: Fewer initial matches, tighter targets
- Level 11+: Locked candies appear (require adjacent match to unlock)

## Visual Design

### Color Palette

```
Background:    #0D0D0D (near black)
Grid lines:    #1A1A1A (dark gray)
Primary:       #00FF00 (neon green)
Secondary:     #00CC00 (darker green)
Accent:        #33FF33 (bright green glow)
Text:          #00FF00 (green) / #FFFFFF (white for emphasis)
Danger:        #FF0000 (red, for virus/warnings)
```

### Candy Sprites (64x64 pixels each)

| Candy | Design |
|-------|--------|
| Black Hat | Silhouette fedora on white circle |
| DEF CON | Official logo, sized to fit |
| Security Ronin | Official logo, sized to fit |
| Lock | Green padlock icon, glowing outline |
| Key | Green skeleton key, glowing |
| Virus | Red/green bug icon, animated wiggle |

### Special Candy Indicators

- Striped: Horizontal/vertical green scan lines across candy
- Wrapped: Pulsing green border + corner brackets
- Color Bomb: Black sphere with green binary rain effect

### UI Elements

- Font: Monospace (Share Tech Mono or similar)
- Scanline overlay (subtle CRT effect)
- Score display: Terminal-style with blinking cursor
- Buttons: Green border, black fill, hover glow

### Background

- Subtle matrix rain (falling green characters, very dim)
- Grid has faint glow effect

## Animations

| Action | Animation | Duration |
|--------|-----------|----------|
| Swap | Candies slide to each other's position | 150ms |
| Invalid swap | Slide halfway, bounce back | 200ms |
| Match clear | Scale up slightly -> particles -> fade out | 300ms |
| Candy fall | Gravity drop with slight bounce at landing | 200ms per row |
| Special create | Flash + glow pulse | 400ms |
| Striped activate | Line sweep across row/column | 250ms |
| Wrapped activate | Expanding ring explosion | 350ms |
| Color bomb activate | All targets pulse, then chain explode | 500ms |
| Cascade | Staggered timing, each chain +100ms delay | Variable |

### Particle Effects

- Match: Small green sparks scatter outward
- Special: Larger particles + screen shake (subtle)
- Combo: Binary digits (0s and 1s) float upward

## Audio

### Sound Effects

| Event | Sound |
|-------|-------|
| Swap | Soft digital "whoosh" |
| Match (3) | Satisfying pop/click |
| Match (4+) | Higher pitch pop + sparkle |
| Striped | Electric zap sweep |
| Wrapped | Bass boom + crackle |
| Color bomb | Deep synthesizer swell |
| Combo chain | Rising pitch sequence |
| Invalid move | Low error buzz |
| Game over | Dramatic power-down |

### Background Music

- Dark ambient cyberpunk track
- ~2-3 minute loop, seamless
- Tempo increases slightly in Time Attack mode

## Leaderboard System

### API Endpoints

```
POST /api/scores
Body: { "handle": "h4x0r", "score": 15000, "mode": "endless" }
Response: { "rank": 42 }

GET /api/scores?mode=endless&limit=10
Response: [{ "handle": "...", "score": ..., "rank": ... }, ...]
```

### Score Submission Flow

1. Game over -> "Enter your handle" prompt (3-12 chars, alphanumeric + underscore)
2. Submit score to API
3. Show player's rank + top 10 leaderboard
4. Option to play again or return to menu

### Anti-Cheat (Basic)

- Server-side score validation (reject impossibly high scores)
- Rate limiting (1 submission per 30 seconds per IP)
- No client-side score storage until verified

## Deployment

### Vercel Configuration

```json
{
  "buildCommand": "pygbag --build src/main.py",
  "outputDirectory": "build/web",
  "functions": {
    "api/scores.py": { "runtime": "python3.11" }
  }
}
```

### Environment Variables

- `KV_REST_API_URL` - Vercel KV endpoint
- `KV_REST_API_TOKEN` - Vercel KV auth token

### Local Development

- Run game: `python src/main.py` (standard Pygame)
- Build for web: `pygbag src/main.py`
- API testing: `vercel dev`

## Asset Sources

| Asset | Source |
|-------|--------|
| Black Hat silhouette | Create from reference image |
| DEF CON logo | `~/Sync/Design Elements/Logos/DEF CON.ai` |
| Security Ronin logo | `~/Sync/Design Elements/Logos/Security Ronin.svg` |
| Lock, Key, Virus icons | Create or source (free icon sets) |
| Sound effects | Generate or source (freesound.org) |
| Background music | Generate or source (royalty-free cyberpunk) |
| Font | Share Tech Mono (Google Fonts, free) |
