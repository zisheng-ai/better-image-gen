# better-image-gen

**A Claude Code skill for AI image generation** — powered by [apiyi](https://api.apiyi.com/register/?aff_code=ijv5), a unified proxy that routes to GPT Image 2, Gemini, Doubao SeedDream, and Nano Banana under a single OpenAI-compatible API.

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
做一张 Mac 动态壁纸，深海珊瑚礁，白天/夜晚切换
```

The skill picks the right model, handles fallbacks, post-processes output, and saves files to `~/.zisheng-ai/`.

---

## Models

Four model families, one API key.

| Alias | Model | Best for | Sizes |
|-------|-------|----------|-------|
| `gpt` *(default)* | `gpt-image-2-all` | Photorealistic photos, portraits, product shots | 30 presets (see below) |
| `gemini` | `gemini-3.1-flash-image-4k` | True 4K output, complex prompts, wallpapers | Free-form |
| `doubao` | `doubao-seedream-5-0-260128` | High-allure content, logos at 1920×1920 | Free-form (≥ 3.7 MP) |
| `nano` | `nano-banana-pro` | Fast drafts, terminal fallback | 1024×1024 |

**Switch models:**
```bash
export APIYI_MODEL=gemini    # use Gemini as primary
export APIYI_MODEL=doubao    # use Doubao as primary
unset  APIYI_MODEL           # reset to default (gpt)
```

**GPT size presets (16:9 tier):**

| Tier | Size |
|------|------|
| 1K   | 1280×720 |
| 2K   | 2048×1152 |
| 4K   | 3840×2160 |

Full 30-preset table in `references/apiyi.md`.

---

## Use Cases

| Request | Model cascade | Output |
|---------|--------------|--------|
| Portrait / illustration | GPT → Doubao → Nano | `.webp` q78, ≤ 300 KB |
| Logo / favicon | Doubao → GPT | `.png` (pngquant), ≤ 100 KB |
| Mac static wallpaper (4K) | GPT → Gemini → Doubao → Nano | `wallpaper.png` (lossless PNG) |
| Mac dynamic wallpaper | GPT → Gemini → Doubao → Nano | `wallpaper-apr.heic` (2-frame, Light/Dark) |
| High-allure content (T3+) | Doubao → Nano | `.webp` q78 |
| Batch (N images) | per-image cascade | N × `.webp`, generated in parallel |

---

## Mac Dynamic Wallpaper

Generates a 2-frame HEIC with `apple_desktop:apr` metadata — macOS switches frames automatically when Light/Dark mode is toggled in System Settings.

```
做一张动态壁纸，深夜星空下的山脉
Make a dynamic wallpaper — underwater coral reef, day and night
```

**Requirements:** `pip3 install pillow-heif` (bundles libheif, no Homebrew needed)

**Output:** `~/.zisheng-ai/dynamic-wallpaper/wallpaper-apr.heic`

> macOS Sonoma note: time-based (h24) HEIC wallpapers no longer work — Apple migrated that format to a private `.madesktop` system. Light/Dark (apr) works fully.

---

## Output Convention

| Asset | Format | Location |
|-------|--------|----------|
| Cover / illustration | Lossy WebP q78 | `~/.zisheng-ai/{name}.webp` |
| Mac static wallpaper | Lossless PNG | `~/.zisheng-ai/wallpaper.png` |
| Mac dynamic wallpaper | 2-frame HEIC | `~/.zisheng-ai/dynamic-wallpaper/wallpaper-apr.heic` |
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
  apiyi.md                    ← API auth, all model specs, size tables, error codes
  generation.md               ← gen_image_apiyi function, cascade logic, batch pattern
  post-process.md             ← WebP conversion, Doubao watermark crop, resize
  dynamic-wallpaper.md        ← Mac dynamic wallpaper: generation + HEIC packaging
```

---

## License

MIT — see [LICENSE](LICENSE).
