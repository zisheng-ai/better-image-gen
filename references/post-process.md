# Post-Processing — GPT Output Conversion

Every generated image must be post-processed before being saved as a deliverable. The only generation model is `gpt-image-2-all`.

---

## Target Format

| Use case | Format | Quality | Target dimensions |
|----------|--------|---------|------------------|
| Hero / cover image | lossy WebP | q78 | varies by use case |
| Inline illustration | lossy WebP | q72 | 664×996 (2:3) |
| Logo / favicon | PNG | n/a | resize to 512×512 after generation |

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

## GPT Image Post-Processing

Output is already at the requested size (e.g. 848×1280 PNG). No resize needed. Convert directly:

```bash
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

After generating a logo or favicon at 1280×1280:

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
