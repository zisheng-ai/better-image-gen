# Portrait / Illustration

Use for portraits, editorial illustrations, book covers, banners, hero images, product-style visuals, and general single-image requests that do not need transparency, wallpaper packaging, or multi-frame output.

Load first:
- `references/generation.md`
- `references/post-process.md`

---

## Defaults

| Field | Value |
|---|---|
| Output directory | `~/Pictures/better-image-gen/` |
| Final format | `.webp` |
| Quality | q78 |
| Primary size | `848x1280` |
| Model flow | GPT primary → GPT retry |

Use user-requested aspect ratio when clear. Otherwise choose:
- Portrait / cover: `848x1280`
- Square social image: `1280x1280`
- Landscape / banner: `1280x720`

---

## Prompt Requirements

Write a complete scene prompt with:
- subject
- setting
- composition
- lighting
- camera or illustration style
- mood
- exclusions: `no text, no watermark, no logo unless requested`

For book covers or ad creatives, make the image scroll-stopping in 0.3 seconds: clear emotion, strong foreground subject, readable world signal.

---

## Pipeline

```bash
OUT_DIR="$HOME/Pictures/better-image-gen"
mkdir -p "$OUT_DIR"
OUTPUT_PATH="/tmp/image_output.png"
FINAL_PATH="$OUT_DIR/${OUTPUT_NAME:-image}.webp"

if   GEN_LOG=$(gen_image_apiyi "$MODEL_GPT" "${REQ_SIZE:-848x1280}" "$OUTPUT_PATH"); then MODEL_USED="$MODEL_GPT"; SIZE="${REQ_SIZE:-848x1280}"
elif GEN_LOG=$(gen_image_apiyi "$MODEL_GPT" "${REQ_SIZE:-848x1280}" "$OUTPUT_PATH"); then MODEL_USED="$MODEL_GPT"; SIZE="${REQ_SIZE:-848x1280}"
else echo "ALL_MODELS_FAILED"; exit 1
fi

GENERATION_MS=$(printf '%s\n' "$GEN_LOG" | awk -F: '/^ELAPSED_MS:/{v=$2} END{print v+0}')
RESPONSE_FORMAT=$(printf '%s\n' "$GEN_LOG" | awk -F: '/^RESPONSE_FORMAT:/{v=$2} END{print v}')

POSTPROCESS_NOTE="direct gpt webp q78"
to_webp "$OUTPUT_PATH" "$FINAL_PATH" 78
rm -f "$OUTPUT_PATH"
write_image_metadata "$FINAL_PATH" "${FINAL_PATH%.*}.json" "$MODEL_USED" "$SIZE" "$GENERATION_MS" "$RESPONSE_FORMAT" "$POSTPROCESS_NOTE"
print_image_summary "${FINAL_PATH%.*}.json"
open "$FINAL_PATH"
```
