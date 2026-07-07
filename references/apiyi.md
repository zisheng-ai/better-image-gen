# APIyi — GPT Image API Reference

OpenAI-compatible image endpoint used by this skill. This skill only uses `gpt-image-2-all`.

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

## Error Handling

| Code | Meaning | Action |
|------|---------|--------|
| `429` | Rate limit | Exponential backoff, retry |
| `5xx` | Content filter or server error | No charge; retry once with softened prompt |
| Timeout | Exceeded `--max-time` | Increase to 360 s, retry once; then fall back to next model |
| `error.message` contains `invalid_prompt` / `safety` / `rejected` | Content safety refusal | Soften prompt, retry once; if still fails move to next model |
