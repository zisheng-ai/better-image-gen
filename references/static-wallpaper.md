# Mac Static Wallpaper

Use for static desktop wallpapers, including MacBook wallpapers, 4K wallpapers, ultrawide wallpapers, and lock-screen style images.

Load first:
- `references/generation.md`

Do not convert wallpapers to WebP. Save lossless PNG.

---

## Defaults

| Field | Value |
|---|---|
| Output directory | `~/Pictures/better-image-gen/` |
| Final file | `wallpaper.png` |
| Final format | PNG |
| Primary size | `3840x2160` |
| Model flow | GPT `3840x2160` → GPT retry |

---

## Pipeline

```bash
OUT_DIR="$HOME/Pictures/better-image-gen"
mkdir -p "$OUT_DIR"
OUTPUT_PATH="/tmp/wallpaper_output.png"
FINAL_PATH="$OUT_DIR/wallpaper.png"

if   GEN_LOG=$(gen_image_apiyi "$MODEL_GPT" "${REQ_SIZE:-3840x2160}" "$OUTPUT_PATH"); then MODEL_USED="$MODEL_GPT"; SIZE="${REQ_SIZE:-3840x2160}"
elif GEN_LOG=$(gen_image_apiyi "$MODEL_GPT" "${REQ_SIZE:-3840x2160}" "$OUTPUT_PATH"); then MODEL_USED="$MODEL_GPT"; SIZE="${REQ_SIZE:-3840x2160}"
else echo "ALL_MODELS_FAILED"; exit 1
fi

GENERATION_MS=$(printf '%s\n' "$GEN_LOG" | awk -F: '/^ELAPSED_MS:/{v=$2} END{print v+0}')
RESPONSE_FORMAT=$(printf '%s\n' "$GEN_LOG" | awk -F: '/^RESPONSE_FORMAT:/{v=$2} END{print v}')

POSTPROCESS_NOTE="lossless gpt png, no webp conversion"
mv "$OUTPUT_PATH" "$FINAL_PATH"
write_image_metadata "$FINAL_PATH" "$OUT_DIR/wallpaper.json" "$MODEL_USED" "$SIZE" "$GENERATION_MS" "$RESPONSE_FORMAT" "$POSTPROCESS_NOTE"
print_image_summary "$OUT_DIR/wallpaper.json"
open "$FINAL_PATH"
```

After opening, ask the user: **「要设置为桌面壁纸吗？」** Wait for confirmation before running:

```bash
osascript -e "tell application \"Finder\" to set desktop picture to POSIX file \"$HOME/Pictures/better-image-gen/wallpaper.png\""
```
