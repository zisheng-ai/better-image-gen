# APIyi — API Reference

Unified image generation proxy exposing multiple models under a single OpenAI-compatible endpoint. This skill uses `gemini-3.1-flash-image-4k` as primary, with `gpt-image-2-all` and `doubao-seedream-5-0-260128` as cascade fallbacks — see `references/generation.md`.

- **Docs:** https://docs.apiyi.com/
- **Sign up:** https://api.apiyi.com/register/?aff_code=ijv5
- **Base URL:** `https://api.apiyi.com/v1` (backup: `https://vip.apiyi.com/v1`)
- **Rate limits:** 3,000 RPM · 1 M TPM · 100 concurrent requests. `429` → exponential backoff.

---

## Authentication

```bash
Authorization: Bearer $APIYI_API_KEY
Content-Type: application/json
```

---

## Environment Variables

| Variable | Values | Default | Effect |
|---|---|---|---|
| `APIYI_API_KEY` | your key | — | **Required.** Auth bearer token. |

---

## Models

### gpt-image-2-all

- **Price:** $0.03 / image (flat, all 30 sizes — 4K included)
- **Generation time:** 90–150 s typical; set `--max-time 300` minimum
- **Sizes:** 30 presets only (10 aspect ratios × 3 resolution tiers). Invalid sizes return an error.
- **Limitations:** no `quality` param, no `n` (one image per call), no inpainting
- **Response:** `b64_json` (includes `data:image/png;base64,` prefix — strip before decoding)

**Complete size table:**

| Ratio | 1K (fast) | 2K | 4K |
|-------|-----------|----|----|
| Square 1:1 | 1280×1280 | 2048×2048 | 2880×2880 |
| Portrait 2:3 | 848×1280 | 1360×2048 | 2336×3520 |
| Landscape 3:2 | 1280×848 | 2048×1360 | 3520×2336 |
| Portrait 3:4 | 960×1280 | 1536×2048 | 2480×3312 |
| Landscape 4:3 | 1280×960 | 2048×1536 | 3312×2480 |
| Social 4:5 | 1024×1280 | 1632×2048 | 2560×3216 |
| Landscape 5:4 | 1280×1024 | 2048×1632 | 3216×2560 |
| Story 9:16 | 720×1280 | 1152×2048 | 2160×3840 |
| Wide 16:9 | 1280×720 | 2048×1152 | 3840×2160 |
| Cinema 21:9 | 1280×544 | 2048×864 | 3840×1632 |

**Minimal request:**

```bash
curl "https://api.apiyi.com/v1/images/generations" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $APIYI_API_KEY" \
  --max-time 300 \
  -d '{
    "model": "gpt-image-2-all",
    "prompt": "...",
    "size": "848x1280"
  }'
```

**Decode b64\_json response:**

```python
import base64, json, sys
data = json.load(sys.stdin)
b64 = data["data"][0]["b64_json"]
if b64.startswith("data:"):          # strip prefix if present
    b64 = b64.split(",", 1)[1]
with open("output.png", "wb") as f:
    f.write(base64.b64decode(b64))
```

---

### gemini-3.1-flash-image-4k

- **Use:** primary model for normal generation
- **Sizes:** free-form — any `WxH` works, no preset constraints
- **Output:** true 4K resolution (~9 MB PNG), no watermark
- **Response:** `b64_json`, raw base64 (no `data:` content prefix — decode directly, no stripping needed)

**Minimal request:**

```bash
curl "https://api.apiyi.com/v1/images/generations" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $APIYI_API_KEY" \
  --max-time 300 \
  -d '{
    "model": "gemini-3.1-flash-image-4k",
    "prompt": "...",
    "size": "3840x2160"
  }'
```

---

### doubao-seedream-5-0-260128

- **Use:** last-resort fallback when both Gemini and GPT fail
- **Price:** lower than gpt-image-2-all
- **Minimum pixel area:** 3,686,400 px (hard error below this floor). Use `1664×2496` for portrait, `1920×1920` for square — request oversized and resize down if the type's target is smaller.
- **Sizes:** free-form; no preset table required
- **Response:** `b64_json` (raw base64, **no** prefix) **or** `url` (CDN link, valid ~24 h)
- **Watermark:** stamps `AI生成` in the bottom-right corner — must crop ~7 % from the bottom after download via `strip_doubao_watermark` in `references/post-process.md`
- **Skip for:** sprite sheets (breaks the frame grid) and transparent logo/icon art (watermark crop + upscale can damage alpha edges)

**Minimal request:**

```bash
curl "https://api.apiyi.com/v1/images/generations" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $APIYI_API_KEY" \
  --max-time 300 \
  -d '{
    "model": "doubao-seedream-5-0-260128",
    "prompt": "...",
    "size": "1664x2496"
  }'
```

---

## Error Handling

| Code | Meaning | Action |
|------|---------|--------|
| `429` | Rate limit | Exponential backoff, retry |
| `5xx` | Content filter or server error | No charge; retry once with softened prompt |
| Timeout | Exceeded `--max-time` | Increase to 360 s, retry once; then fall back to next model |
| `error.message` contains `invalid_prompt` / `safety` / `rejected` | Content safety refusal | Soften prompt, retry once; if still fails move to next model |
