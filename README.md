# apiyi-image-gen

A Claude Code skill for AI image generation via [apiyi](https://api.apiyi.com/register/?aff_code=ijv5) — a unified proxy that exposes GPT Image 2, Doubao SeedDream, and other models under a single OpenAI-compatible API.

## Features

- **Model cascade**: GPT Image 2 → Doubao SeedDream → Nano Banana, with retry logic
- **Parallel batch generation**: fire all images concurrently, `wait` for results
- **Auto post-processing**: WebP conversion, Doubao watermark removal, resize by model
- **Mac wallpaper**: static 4K PNG + dynamic Light/Dark HEIC (apr format, Sonoma compatible)

## Setup

1. Get an API key at https://api.apiyi.com/register/?aff_code=ijv5
2. Export the key:
   ```bash
   export APIYI_API_KEY="your-key"
   ```
3. Install this skill in Claude Code:
   ```bash
   git clone https://github.com/zisheng-ai/apiyi-image-gen ~/.claude/skills/apiyi-image-gen
   ```

## Usage

Once installed, Claude Code triggers this skill automatically when you ask to generate images:

```
Generate a portrait photo of a professional woman in a modern office
Create a square logo for my app — minimalist, dark theme
Generate 5 product images in parallel for my e-commerce site
做一张 Mac 动态壁纸，白天/夜晚主题
```

## Use Cases

| Use case | Output | API calls |
|---|---|---|
| Portrait / illustration | `.webp` q78 | 1 |
| Logo / favicon | `.png` (pngquant) | 1 |
| Mac static wallpaper | `wallpaper.png` (4K, lossless) | 1 |
| Mac dynamic wallpaper | `wallpaper-apr.heic` (2 frames, light/dark) | 2 |
| Batch generation | N × `.webp` in parallel | N |

## Mac Dynamic Wallpaper

Generates a 2-frame HEIC with `apple_desktop:apr` metadata. macOS automatically switches between frames when Light/Dark mode is toggled.

```
做一张动态壁纸，主题是星空下的山脉
```

Requirements: `pip3 install pillow-heif` (no Homebrew needed, pillow-heif bundles libheif).

Output: `~/.zisheng-ai/dynamic-wallpaper/wallpaper-apr.heic`

## Output Convention

| Asset | Format | Notes |
|---|---|---|
| Cover / illustration | lossy WebP q78 | ≤ 300 KB target |
| Mac static wallpaper | lossless PNG | no WebP conversion |
| Mac dynamic wallpaper | 2-frame HEIC | no WebP conversion |
| Logo | PNG (pngquant) | ≤ 100 KB target |

## Models

| Alias | Model ID | Best for |
|---|---|---|
| `gpt` (default) | `gpt-image-2-all` | Photorealistic photos, portraits |
| `doubao` | `doubao-seedream-5-0-260128` | High-allure content; logos at 1920×1920 |
| `nano` | `nano-banana-pro` | Fast drafts, terminal fallback |

```bash
export APIYI_MODEL=doubao   # force doubao as primary
unset APIYI_MODEL           # reset to default (gpt)
```

## File Structure

```
SKILL.md                        ← skill entry point
references/
  apiyi.md                      ← API auth, model specs, error codes
  generation.md                 ← gen_image_apiyi function, cascade, batch pattern
  post-process.md               ← WebP conversion, resize, Doubao watermark crop
  dynamic-wallpaper.md          ← Mac dynamic wallpaper (apr): generation + HEIC packaging
```

## License

MIT
