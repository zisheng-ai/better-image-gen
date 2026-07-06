# apiyi-image-gen

A Claude Code skill for AI image generation via [apiyi](https://api.apiyi.com/register/?aff_code=ijv5) — a unified proxy that exposes GPT Image 2, Doubao SeedDream, and other models under a single OpenAI-compatible API.

## Features

- **Model cascade**: GPT Image 2 (primary) → Doubao SeedDream (fallback / high-allure) → Nano Banana (terminal fallback)
- **Parallel batch generation**: fire all images concurrently, `wait` for results
- **Auto post-processing**: WebP conversion, Doubao watermark removal, resize by model
- **Hardcoded to apiyi**: one key, one endpoint, three models

## Setup

1. Get an API key at https://api.apiyi.com/register/?aff_code=ijv5
2. Export the key:
   ```bash
   export APIYI_API_KEY="your-key"
   ```
3. Install this skill in Claude Code:
   ```bash
   # As a git submodule (recommended)
   git submodule add https://github.com/zisheng-ai/apiyi-image-gen .claude/skills/apiyi-image-gen
   ```
   Or clone standalone:
   ```bash
   git clone https://github.com/zisheng-ai/apiyi-image-gen ~/.claude/skills/apiyi-image-gen
   ```

## Usage

Once installed, Claude Code will automatically use this skill when you ask to generate images:

> "Generate a portrait photo of a professional woman in a modern office"

> "Create a square logo for my app — minimalist, dark theme"

> "Generate 5 product images in parallel for my e-commerce site"

The skill handles model selection, cascade fallback, post-processing, and metadata output automatically.

## File Structure

```
SKILL.md                    ← skill entry point (loaded by Claude Code)
references/
  apiyi.md                  ← API auth, all model specs, error handling
  generation.md             ← gen_image_apiyi function, cascade, batch pattern
  post-process.md           ← WebP conversion, resize, Doubao watermark crop
```

## Output Convention

Every image is delivered as:
- `{name}.webp` — lossy WebP (q78), ≤ 300 KB
- `{name}.json` — metadata: model used, size, prompt

Intermediate PNGs are written to `/tmp/` and deleted after conversion.

## Models

| Model | ID | Best for |
|---|---|---|
| gpt-image-2 | `gpt-image-2-all` | Photorealistic photos and portraits |
| doubao-seedream-5 | `doubao-seedream-5-0-260128` | High-allure content; logos at 1920×1920 |
| nano-banana-pro | `nano-banana-pro` | Blank prevention only |

See `references/apiyi.md` for pricing, size tables, and error codes.

## License

MIT
