# better-image-gen

**A multi-model AI image generation Skill** — powered by [apiyi](https://api.apiyi.com/register/?aff_code=ijv5), with automatic GPT, Gemini, and Doubao fallback through an OpenAI-compatible image API.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Skill-blueviolet)](https://claude.ai/code)
[![apiyi](https://img.shields.io/badge/Powered_by-apiyi-orange)](https://api.apiyi.com/register/?aff_code=ijv5)

[English](#) · [中文](README.zh-CN.md)

---

## What It Does

Invoke naturally in Claude Code — no commands, no config per-session:

```
Generate a cinematic portrait of a woman in a Tokyo street at night
Make a square logo for my app, dark theme, minimalist
Create 8 product images in parallel for my store
Make a RunCat-style menu bar sprite loop of a tiny robot running
做一张 Mac 动态壁纸，深海珊瑚礁，白天/夜晚切换
```

The skill routes each image type to the right workflow, tries GPT first, automatically falls back to Gemini and then Doubao when needed, post-processes output, and saves files to `~/Pictures/better-image-gen/`.

It also applies a prompt compliance layer before generation: prompts are normalized away from platform logos, exact in-image text, explicit content, graphic violence, and living-artist imitation so routine creative requests are less likely to be rejected accidentally.

---

## Model

| Model | Role | Notes |
|-------|------|-------|
| `gpt-image-2-all` | Primary | Best prompt adherence and photorealism; 30 size presets |
| `gemini-3.1-flash-image-4k` | First fallback | Free-form sizes, no watermark, true 4K |
| `doubao-seedream-5-0-260128` | Last-resort fallback | Watermarked output is auto-cropped; pixel-area floor applies |

**GPT size presets (16:9 tier):**

| Tier | Size |
|------|------|
| 1K   | 1280×720 |
| 2K   | 2048×1152 |
| 4K   | 3840×2160 |

Full model specifications and size constraints are in `references/apiyi.md`.

---

## Use Cases

| Request | Model | Output |
|---------|--------------|--------|
| Portrait / illustration | GPT → Gemini → Doubao | `.webp` q78, ≤ 300 KB |
| Logo / favicon | GPT → Gemini | `.png` (pngquant), ≤ 100 KB |
| Mac static wallpaper (4K) | GPT → Gemini → Doubao | `wallpaper.png` (lossless PNG) |
| Mac dynamic wallpaper | GPT → Gemini → Doubao per frame | `wallpaper-apr.heic` (2-frame, Light/Dark) |
| Sprite loop | GPT → Gemini | numbered PNG frames + `preview.gif` |
| Batch (N images) | Cascade per image | N × `.webp`, generated in parallel |

---

## Mac Dynamic Wallpaper

Generates a 2-frame HEIC with `apple_desktop:apr` metadata — macOS switches frames automatically when Light/Dark mode is toggled in System Settings.

```
做一张动态壁纸，深夜星空下的山脉
Make a dynamic wallpaper — underwater coral reef, day and night
```

**Requirements:** `pip3 install pillow-heif` (bundles libheif, no Homebrew needed)

**Output:** `~/Pictures/better-image-gen/dynamic-wallpaper/wallpaper-apr.heic`

> macOS Sonoma note: time-based (h24) HEIC wallpapers no longer work — Apple migrated that format to a private `.madesktop` system. Light/Dark (apr) works fully.

---

## Sprite Loop

Use for RunCat-like frame animations, menu-bar status mascots, loading loops, and tiny app animations. The skill generates a sprite sheet, splits it into numbered PNG frames, writes `manifest.json`, and opens `preview.gif`.

**Output:** `~/Pictures/better-image-gen/sprite-loop/{name}/`

---

## Output Convention

| Asset | Format | Location |
|-------|--------|----------|
| Cover / illustration | Lossy WebP q78 | `~/Pictures/better-image-gen/{name}.webp` |
| Mac static wallpaper | Lossless PNG | `~/Pictures/better-image-gen/wallpaper.png` |
| Mac dynamic wallpaper | 2-frame HEIC | `~/Pictures/better-image-gen/dynamic-wallpaper/wallpaper-apr.heic` |
| Sprite loop | PNG frames + preview GIF | `~/Pictures/better-image-gen/sprite-loop/{name}/` |
| Logo | PNG (pngquant) | project-local |
| Metadata | JSON | alongside each image |

Intermediate PNGs are written to `/tmp/` and cleaned up after packaging.

---

## Setup

**1. Get an API key**

Register at [apiyi.com](https://api.apiyi.com/register/?aff_code=ijv5) — new accounts get free credits.

**2. Export the key**
```bash
export APIYI_API_KEY="your-key-here"
# Add to ~/.zshrc to persist across sessions
```

**3. Install the skill**
```bash
git clone https://github.com/zisheng-ai/apiyi-image-gen ~/.claude/skills/apiyi-image-gen
```

**4. (Dynamic wallpaper only)**
```bash
pip3 install pillow-heif
```

---

## File Structure

```
SKILL.md                      ← skill entry point & trigger rules
references/
  apiyi.md                    ← API auth, model specs, size constraints, error codes
  generation.md               ← API key check, model aliases, gen_image_apiyi, metadata helpers
  prompt-compliance.md        ← prompt normalization and rejection retry policy
  post-process.md             ← WebP conversion, resize, PNG compression
  portrait.md                 ← portraits, covers, banners, general single images
  high-allure.md              ← suggestive romance/editorial images
  logo-icon.md                ← transparent logos, icons, favicons, cutouts
  static-wallpaper.md         ← static wallpaper PNG pipeline
  dynamic-wallpaper.md        ← Mac dynamic wallpaper: generation + HEIC packaging
  sprite-loop.md              ← RunCat-like frame animation assets
```

---

## License

MIT — see [LICENSE](LICENSE).
