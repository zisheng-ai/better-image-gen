# Post-Processing — Resize, Crop, WebP Conversion

Every generated image must be post-processed before being saved as a deliverable. Steps differ by model.

---

## Target Format

| Use case | Format | Quality | Target dimensions |
|----------|--------|---------|------------------|
| Hero / cover image | lossy WebP | q78 | varies by use case |
| Inline illustration | lossy WebP | q72 | 664×996 (2:3) |
| Logo / favicon | lossless or lossy WebP | q85 | resize to 512×512 after generation |

**Never use lossless WebP for photographic content** — it is ~3× larger than lossy. Always use lossy.

---

## WebP Conversion Function

Prefer `cwebp` (fastest); fall back to Pillow. If the WebP output is larger than the source, discard it and copy the PNG.

```bash
to_webp() {
  local src="$1" dst="$2" q="${3:-78}"
  local before after
  before=$(stat -f%z "$src" 2>/dev/null || stat -c%s "$src")
  if command -v cwebp &>/dev/null; then
    cwebp -quiet -q "$q" "$src" -o "$dst"
  else
    python3 -c "from PIL import Image; im=Image.open('$src'); im.save('$dst','webp',quality=$q,method=6)"
  fi
  after=$(stat -f%z "$dst" 2>/dev/null || stat -c%s "$dst")
  if [ "$after" -ge "$before" ]; then
    rm -f "$dst"
    cp "$src" "$dst"
    echo "⚠ webp larger than src (${after}B ≥ ${before}B) — kept original"
  else
    echo "✓ webp q${q}: ${before}B → ${after}B (-$(( (before-after)*100/before ))%)"
  fi
}
```

Install `cwebp` if missing:
```bash
command -v cwebp &>/dev/null || brew install webp -q
```

---

## Post-Process by Model

### gpt-image-2-all

Output is already at the requested size (e.g. 848×1280 PNG). No resize needed. Convert directly:

```bash
to_webp "$OUTPUT_PATH" "output.webp" 78
rm -f "$OUTPUT_PATH"
```

### doubao-seedream-5-0-260128

Stamps an `AI生成` watermark in the bottom-right corner. Crop ~7 % from the bottom, then resize to target, then convert:

```bash
# 1. Crop watermark: keep top 93% of height, full width
w=$(python3 -c "from PIL import Image; print(Image.open('$OUTPUT_PATH').size[0])")
h=$(python3 -c "from PIL import Image; print(Image.open('$OUTPUT_PATH').size[1])")
sips -c $((h * 93 / 100)) $w "$OUTPUT_PATH"   # crops in-place (top-center crop)

# 2. Resize to target (e.g. 848x1280)
sips -z 1280 848 "$OUTPUT_PATH"

# 3. Convert
to_webp "$OUTPUT_PATH" "output.webp" 78
rm -f "$OUTPUT_PATH"
```

If `sips` is not available (Linux), use Pillow:

```python
from PIL import Image
img = Image.open("output.png")
w, h = img.size
img = img.crop((0, 0, w, int(h * 0.93)))    # remove bottom 7%
img = img.resize((848, 1280), Image.LANCZOS)
img.save("output.png")
```

Doubao watermark is typically in the bottom ~5–7 %. If it is still visible after 7 % crop, increase to 10 %.

### nano-banana-pro

Output is square 1024×1024. Center-crop to 2:3, then resize:

```bash
sips -c 1024 683 "$OUTPUT_PATH"    # crop width to get 683x1024 (≈2:3), centered
sips -z 1280 848 "$OUTPUT_PATH"    # resize to 848x1280
to_webp "$OUTPUT_PATH" "output.webp" 78
rm -f "$OUTPUT_PATH"
```

---

## Logo Post-Processing

For logo/icon/favicons where transparency is expected, verify alpha before resizing:

```bash
sips -g hasAlpha "$OUTPUT_PATH"
```

If the output has black/white corners, a solid square background, or a baked rounded rectangle tile, remove only the edge-connected background before resizing. For the Argos local tool:

```bash
swift run --package-path /Users/zisheng/github/argos transparentize-black-background \
  "$OUTPUT_PATH" /tmp/logo-transparent.png --threshold 18
mv /tmp/logo-transparent.png "$OUTPUT_PATH"
sips -g hasAlpha "$OUTPUT_PATH"
```

Do not use a global color erase on logos by default; it can damage black/white details inside the mark. Prefer edge-connected background removal so interior dark/light details remain opaque.

After generating a logo or favicon at 1920×1920 (doubao) or 1280×1280 (GPT):

```bash
# Resize and compress logo
sips -z 512 512 public/logo.png
pngquant --force --quality=80-95 --speed 1 --output public/logo.png public/logo.png

# Resize and compress favicon
sips -z 256 256 public/favicon.png
pngquant --force --quality=80-95 --speed 1 --output public/favicon.png public/favicon.png
```

Target sizes: logo ≤ 100 KB, favicon ≤ 25 KB. Raw generated files are typically 700 KB–1.3 MB without compression.

---

## File Size Budget

| Asset type | Hard limit | Action if exceeded |
|------------|------------|-------------------|
| Cover / hero WebP | 300 KB | Lower quality to q70, retry; or resize to 683×1024 and re-convert |
| Illustration WebP | 300 KB | Lower quality to q65 and re-convert |
| Logo PNG | 100 KB | Re-run `pngquant` at `--quality=60-80` |
| Favicon PNG | 25 KB | Re-run `pngquant` at `--quality=50-70` |

---

## Full Single-Image Pipeline Example

```bash
# 1. Set your prompt
PROMPT="photorealistic portrait, shot on Canon EOS R5 with 85mm f/1.4 lens, ..."

# 2. Generate
OUTPUT_PATH="/tmp/image_output.png"
if   GEN_LOG=$(gen_image_apiyi "gpt-image-2-all"            "848x1280"  "$OUTPUT_PATH"); then MODEL_USED="gpt-image-2-all";            SIZE="848x1280"
elif GEN_LOG=$(gen_image_apiyi "doubao-seedream-5-0-260128" "1664x2496" "$OUTPUT_PATH"); then MODEL_USED="doubao-seedream-5-0-260128"; SIZE="1664x2496"
elif GEN_LOG=$(gen_image_apiyi "nano-banana-pro"            "1024x1024" "$OUTPUT_PATH"); then MODEL_USED="nano-banana-pro";            SIZE="1024x1024"
else echo "ALL_MODELS_FAILED"; exit 1; fi
GENERATION_MS=$(printf '%s\n' "$GEN_LOG" | awk -F: '/^ELAPSED_MS:/{v=$2} END{print v+0}')
RESPONSE_FORMAT=$(printf '%s\n' "$GEN_LOG" | awk -F: '/^RESPONSE_FORMAT:/{v=$2} END{print v}')

# 3. Post-process by model
OUT_DIR="$HOME/Pictures/better-image-gen"
mkdir -p "$OUT_DIR"
FINAL="$OUT_DIR/image.webp"
case "$MODEL_USED" in
  gpt-image-2-all)
    POSTPROCESS_NOTE="direct webp q78"
    to_webp "$OUTPUT_PATH" "$FINAL" 78 ;;
  doubao-seedream-5-0-260128)
    h=$(python3 -c "from PIL import Image; print(Image.open('$OUTPUT_PATH').size[1])")
    w=$(python3 -c "from PIL import Image; print(Image.open('$OUTPUT_PATH').size[0])")
    sips -c $((h * 93 / 100)) $w "$OUTPUT_PATH"
    sips -z 1280 848 "$OUTPUT_PATH"
    POSTPROCESS_NOTE="crop bottom 7 percent, resize 848x1280, webp q78"
    to_webp "$OUTPUT_PATH" "$FINAL" 78 ;;
  nano-banana-pro)
    sips -c 1024 683 "$OUTPUT_PATH"
    sips -z 1280 848 "$OUTPUT_PATH"
    POSTPROCESS_NOTE="center crop 2:3, resize 848x1280, webp q78"
    to_webp "$OUTPUT_PATH" "$FINAL" 78 ;;
esac
rm -f "$OUTPUT_PATH"

# 4. Save metadata
write_image_metadata "$FINAL" "$OUT_DIR/image.json" "$MODEL_USED" "$SIZE" "$GENERATION_MS" "$RESPONSE_FORMAT" "$POSTPROCESS_NOTE"
print_image_summary "$OUT_DIR/image.json"

echo "✓ $FINAL ($(stat -f%z "$FINAL" 2>/dev/null || stat -c%s "$FINAL") bytes)"
open "$FINAL"
```
